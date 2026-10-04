"""Server-side Kite session exchange and one-attempt manual limit-order submission."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import sqlite3
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from quantlab.broker_gateway.secrets import account_id_hash
from quantlab.kite_execution_gateway.config import KiteExecutionGatewayConfig
from quantlab.kite_execution_gateway.models import (
    ManualLimitOrder,
    ManualOrderPreview,
    ManualOrderSubmission,
    ManualSubmissionResult,
    SubmissionState,
)
from quantlab.realtime_data.hashing import sha256

_KITE_API = "https://api.kite.trade"
_KITE_LOGIN = "https://kite.zerodha.com/connect/login?v=3"


class GatewayError(RuntimeError):
    """Safe-to-display gateway failure; it never contains request or token material."""


class GatewayTimeout(TimeoutError):
    """The provider may have received the request; it must never be retried automatically."""


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes


class KiteTransport:
    """Fixed-host transport used only by the remote gateway process."""

    def request(
        self, method: str, path: str, headers: Mapping[str, str], body: bytes = b""
    ) -> HttpResponse:
        request = Request(
            f"{_KITE_API}{path}", data=body or None, headers=dict(headers), method=method
        )
        try:
            with urlopen(request, timeout=10) as response:  # noqa: S310 - fixed HTTPS host
                return HttpResponse(int(response.status), response.read())
        except HTTPError as exc:
            return HttpResponse(int(exc.code), exc.read())
        except URLError as exc:
            raise GatewayTimeout(f"Kite network failure: {type(exc.reason).__name__}") from None


class SubmissionJournal:
    """Durable idempotency and audit record; tokens and TOTP values are never stored."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._lock = Lock()
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS manual_submissions (
               idempotency_key TEXT PRIMARY KEY, intent_hash TEXT NOT NULL,
               state TEXT NOT NULL, broker_order_id TEXT NOT NULL DEFAULT '',
               detail TEXT NOT NULL DEFAULT '', attempted_at TEXT NOT NULL,
               totp_window INTEGER NOT NULL UNIQUE)"""
        )
        self._conn.commit()

    def get(self, key: str) -> ManualSubmissionResult | None:
        row = self._conn.execute(
            "SELECT intent_hash, idempotency_key, state, broker_order_id, detail, attempted_at "
            "FROM manual_submissions WHERE idempotency_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        return ManualSubmissionResult(
            intent_hash=str(row[0]),
            idempotency_key=str(row[1]),
            state=SubmissionState(str(row[2])),
            broker_order_id=str(row[3]),
            detail=str(row[4]),
            attempted_at=datetime.fromisoformat(str(row[5])),
        )

    def begin(self, result: ManualSubmissionResult, *, totp_window: int) -> None:
        with self._lock:
            try:
                self._conn.execute(
                    "INSERT INTO manual_submissions "
                    "(idempotency_key, intent_hash, state, attempted_at, totp_window) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        result.idempotency_key,
                        result.intent_hash,
                        result.state.value,
                        result.attempted_at.isoformat(),
                        totp_window,
                    ),
                )
                self._conn.commit()
            except sqlite3.IntegrityError as exc:
                raise GatewayError("duplicate submission or already-used TOTP window") from exc

    def finish(self, result: ManualSubmissionResult) -> ManualSubmissionResult:
        with self._lock:
            self._conn.execute(
                "UPDATE manual_submissions SET state = ?, broker_order_id = ?, detail = ? "
                "WHERE idempotency_key = ?",
                (result.state.value, result.broker_order_id, result.detail, result.idempotency_key),
            )
            self._conn.commit()
        return result


class SecureKiteExecutionGateway:
    """Remote manual gateway. It permits no market, modify, cancel, or batch operation."""

    def __init__(
        self,
        config: KiteExecutionGatewayConfig,
        *,
        transport: KiteTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        config.validate()
        self._config = config
        self._transport = transport or KiteTransport()
        self._clock = clock or (lambda: datetime.now(tz=UTC))
        self._access_token = ""
        self._journal = SubmissionJournal(config.journal_path)

    def login_url(self) -> str:
        return f"{_KITE_LOGIN}&{urlencode({'api_key': self._config.api_key})}"

    def authenticate_request_token(self, request_token: str) -> None:
        if not request_token:
            raise GatewayError("Kite authentication response was missing request_token")
        checksum = hashlib.sha256(
            f"{self._config.api_key}{request_token}{self._config.api_secret}".encode()
        ).hexdigest()
        response = self._transport.request(
            "POST",
            "/session/token",
            {"X-Kite-Version": "3", "Content-Type": "application/x-www-form-urlencoded"},
            urlencode(
                {
                    "api_key": self._config.api_key,
                    "request_token": request_token,
                    "checksum": checksum,
                }
            ).encode(),
        )
        data = self._response_data(response, "Kite session exchange")
        access_token = data.get("access_token")
        user_id = data.get("user_id")
        if not isinstance(access_token, str) or not isinstance(user_id, str):
            raise GatewayError("Kite session response was incomplete")
        if not hmac.compare_digest(
            account_id_hash(user_id), self._config.expected_account_fingerprint
        ):
            raise GatewayError(
                "Kite account identity does not match the configured execution account"
            )
        self._access_token = access_token

    def ready(self) -> bool:
        return bool(self._access_token) and self._config.execution_enabled

    def preview(self, order: ManualLimitOrder) -> ManualOrderPreview:
        self._validate_order(order)
        digest = self.intent_hash(order)
        return ManualOrderPreview(
            intent_hash=digest,
            confirmation_text=f"CONFIRM {digest}",
            estimated_notional=order.quantity * order.price,
            expires_at=order.expires_at,
        )

    def submit(self, submission: ManualOrderSubmission) -> ManualSubmissionResult:
        order = submission.order
        preview = self.preview(order)
        if not self._config.execution_enabled:
            raise GatewayError("execution gateway is disabled by server policy")
        if not self._access_token:
            raise GatewayError("Kite session is not authenticated on the execution gateway")
        if (
            submission.intent_hash != preview.intent_hash
            or submission.confirmation_text != preview.confirmation_text
        ):
            raise GatewayError("confirmation does not match the exact immutable order")
        now = self._now()
        if order.expires_at <= now:
            raise GatewayError("order preview has expired; create a new preview")
        window = self._verify_totp(submission.totp_code, now)
        existing = self._journal.get(order.idempotency_key)
        if existing is not None:
            if existing.intent_hash != preview.intent_hash:
                raise GatewayError("idempotency key is bound to a different order")
            return existing
        attempting = ManualSubmissionResult(
            intent_hash=preview.intent_hash,
            idempotency_key=order.idempotency_key,
            state=SubmissionState.SUBMITTING,
            attempted_at=now,
        )
        self._journal.begin(attempting, totp_window=window)
        try:
            response = self._transport.request(
                "POST",
                "/orders/regular",
                {
                    "X-Kite-Version": "3",
                    "Authorization": f"token {self._config.api_key}:{self._access_token}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                urlencode(
                    {
                        "exchange": order.exchange,
                        "tradingsymbol": order.tradingsymbol,
                        "transaction_type": order.transaction_type,
                        "quantity": str(order.quantity),
                        "product": order.product,
                        "order_type": order.order_type,
                        "price": str(order.price),
                        "validity": order.validity,
                    }
                ).encode(),
            )
        except GatewayTimeout:
            return self._journal.finish(
                attempting.model_copy(
                    update={
                        "state": SubmissionState.SUBMISSION_UNKNOWN,
                        "detail": (
                            "network outcome unknown; reconcile read-only before any further action"
                        ),
                    }
                )
            )
        if not 200 <= response.status < 300:
            return self._journal.finish(
                attempting.model_copy(
                    update={"state": SubmissionState.REJECTED, "detail": "Kite rejected the order"}
                )
            )
        data = self._response_data(response, "Kite order")
        nested = data.get("order_id")
        if not isinstance(nested, str) or not nested:
            return self._journal.finish(
                attempting.model_copy(
                    update={
                        "state": SubmissionState.SUBMISSION_UNKNOWN,
                        "detail": (
                            "Kite response did not contain an order identifier; reconcile read-only"
                        ),
                    }
                )
            )
        return self._journal.finish(
            attempting.model_copy(
                update={
                    "state": SubmissionState.ACKNOWLEDGED,
                    "broker_order_id": nested,
                    "detail": (
                        "Kite accepted the request; order execution must be observed separately"
                    ),
                }
            )
        )

    @staticmethod
    def intent_hash(order: ManualLimitOrder) -> str:
        return sha256(order.model_dump(mode="json"))

    def _validate_order(self, order: ManualLimitOrder) -> None:
        if order.account_fingerprint != self._config.expected_account_fingerprint:
            raise GatewayError("order account does not match the configured execution account")
        if order.exchange != "NSE" or order.product != "CNC" or order.order_type != "LIMIT":
            raise GatewayError("only NSE CNC LIMIT orders are permitted by this gateway")
        if order.transaction_type not in {"BUY", "SELL"}:
            raise GatewayError("order side must be BUY or SELL")
        if order.validity != "DAY":
            raise GatewayError("only DAY validity is permitted")
        symbol = f"{order.exchange}:{order.tradingsymbol}".upper()
        if symbol not in self._config.allowed_symbols:
            raise GatewayError("symbol is outside the explicit server allowlist")
        if order.quantity * order.price > self._config.max_notional:
            raise GatewayError("order notional exceeds the server-side limit")
        if order.expires_at <= order.created_at:
            raise GatewayError("order expiry must be after its creation time")

    def _verify_totp(self, code: str, now: datetime) -> int:
        counter = int(now.timestamp() // 30)
        for candidate in (counter, counter - 1):
            if hmac.compare_digest(code, _totp(self._config.operator_totp_secret, candidate)):
                return candidate
        raise GatewayError("invalid or expired operator TOTP")

    def _response_data(self, response: HttpResponse, operation: str) -> dict[str, object]:
        if not 200 <= response.status < 300:
            raise GatewayError(f"{operation} failed ({response.status})")
        try:
            decoded = json.loads(response.body.decode())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GatewayError(f"{operation} returned invalid JSON") from exc
        if not isinstance(decoded, dict) or decoded.get("status") != "success":
            raise GatewayError(f"{operation} was not accepted")
        data = decoded.get("data")
        if not isinstance(data, dict):
            raise GatewayError(f"{operation} returned malformed data")
        return data

    def _now(self) -> datetime:
        now = self._clock()
        return now if now.tzinfo is not None else now.replace(tzinfo=UTC)


def _totp(secret: str, counter: int) -> str:
    try:
        key = base64.b32decode(secret.upper().replace(" ", ""), casefold=True)
    except (ValueError, binascii.Error) as exc:
        raise GatewayError("execution gateway TOTP secret is malformed") from exc
    digest = hmac.new(key, counter.to_bytes(8, "big"), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = int.from_bytes(digest[offset : offset + 4], "big") & 0x7FFFFFFF
    return f"{binary % 1_000_000:06d}"
