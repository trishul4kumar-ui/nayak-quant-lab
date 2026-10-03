"""Kite Connect v3 account observer. This module has no broker-write capability."""

from __future__ import annotations

import csv
import io
import json
import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from quantlab.broker_gateway.errors import BrokerGatewayError, BrokerWriteError
from quantlab.broker_gateway.models import (
    BrokerAccountSnapshot,
    BrokerFillSnapshot,
    BrokerHealth,
    BrokerHoldingSnapshot,
    BrokerMarginSnapshot,
    BrokerOrderSnapshot,
    BrokerPositionSnapshot,
    BrokerProfileSnapshot,
    GatewaySnapshotBundle,
    InstrumentMapping,
    Provenance,
)
from quantlab.broker_gateway.secrets import account_id_hash
from quantlab.data.fabric.checksums import sha256_bytes
from quantlab.data.fabric.instruments import InstrumentMaster

_BASE_URL = "https://api.kite.trade"
_SCHEMA = "3.2.0"
_RETRYABLE = frozenset({408, 429, 500, 502, 503, 504})


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes
    headers: Mapping[str, str]


class ReadOnlyTransport(Protocol):
    """Minimal GET-only boundary. Implementations cannot receive an HTTP method."""

    def get(
        self, path: str, headers: Mapping[str, str], timeout_seconds: float
    ) -> HttpResponse: ...


class UrllibReadOnlyTransport:
    """Production transport. It constructs only GET requests against Kite's fixed base URL."""

    def get(self, path: str, headers: Mapping[str, str], timeout_seconds: float) -> HttpResponse:
        request = Request(f"{_BASE_URL}{path}", headers=dict(headers), method="GET")
        try:
            with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed HTTPS host
                return HttpResponse(
                    status=int(response.status),
                    body=response.read(),
                    headers=dict(response.headers.items()),
                )
        except HTTPError as exc:
            return HttpResponse(
                status=int(exc.code),
                body=exc.read(),
                headers=dict(exc.headers.items()) if exc.headers is not None else {},
            )
        except URLError as exc:
            raise BrokerGatewayError(f"kite network failure: {type(exc.reason).__name__}") from None


class KiteReadOnlyConfig(BaseSettings):
    """Environment-only credentials; values never enter snapshots, logs, or errors."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_key: str = Field(default="", validation_alias=AliasChoices("KITE_API_KEY", "api_key"))
    access_token: str = Field(
        default="", validation_alias=AliasChoices("KITE_ACCESS_TOKEN", "access_token")
    )
    timeout_seconds: float = Field(default=10.0, validation_alias="KITE_TIMEOUT_SECONDS")
    max_attempts: int = Field(default=3, validation_alias="KITE_MAX_ATTEMPTS", ge=1, le=5)
    stale_after_seconds: float = Field(
        default=60.0, validation_alias="KITE_STALE_AFTER_SECONDS", gt=0
    )


class KiteReadOnlyAdapter:
    """Kite v3 observer using documented read endpoints only; never an order client."""

    adapter_id = "kite-readonly-v3"
    broker = "zerodha"

    def __init__(
        self,
        config: KiteReadOnlyConfig,
        *,
        transport: ReadOnlyTransport | None = None,
        instrument_master: InstrumentMaster | None = None,
        clock: Callable[[], datetime] | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        if not config.api_key or not config.access_token:
            raise BrokerGatewayError("Kite credentials are not configured")
        self._config = config
        self._transport = transport or UrllibReadOnlyTransport()
        self._master = instrument_master
        self._clock = clock or (lambda: datetime.now(tz=UTC))
        self._sleep = sleeper or time.sleep
        self._connected = False
        self._auth_state = "auth_required"
        self._sequence = 0
        self._last_observed_at: datetime | None = None
        self._account_hash = account_id_hash("kite-unobserved")
        self._mappings: dict[str, InstrumentMapping] = {}

    @classmethod
    def from_environment(cls) -> KiteReadOnlyAdapter:
        return cls(KiteReadOnlyConfig())

    @property
    def auth_state(self) -> str:
        return self._auth_state

    def connect(self) -> BrokerHealth:
        self._auth_state = "authenticating"
        try:
            self.profile()
        except BrokerGatewayError:
            self._connected = False
            if self._auth_state == "authenticating":
                self._auth_state = "error"
            raise
        self._connected = True
        self._auth_state = "connected"
        return self.health()

    def disconnect(self) -> BrokerHealth:
        # Deliberately do not call Kite's DELETE /session/token: it is a write-like mutation.
        self._connected = False
        self._auth_state = "disconnected"
        return self.health()

    def health(self) -> BrokerHealth:
        now = self._now()
        stale = (
            self._last_observed_at is None
            or (now - self._last_observed_at).total_seconds() > self._config.stale_after_seconds
        )
        state = "connected_read_only" if self._connected and not stale else self._auth_state
        return BrokerHealth(
            state=state,
            healthy=self._connected and not stale,
            stale=stale,
            broker_connected=self._connected,
            note="Kite read-only observation. Connected does not authorize trading.",
        )

    def profile(self) -> BrokerProfileSnapshot:
        data, digest, captured = self._json("/user/profile")
        user_id = self._required_str(data, "user_id", "profile")
        self._account_hash = account_id_hash(user_id)
        return BrokerProfileSnapshot(
            snapshot_id=f"kite-profile-{digest[:12]}",
            broker=self.broker,
            account_id_hash=self._account_hash,
            captured_at=captured,
            payload_hash=digest,
            exchanges=self._string_tuple(data.get("exchanges")),
            products=self._string_tuple(data.get("products")),
            order_types=self._string_tuple(data.get("order_types")),
            user_type=str(data.get("user_type") or "unknown"),
        )

    def account(self) -> BrokerAccountSnapshot:
        data, digest, captured = self._json("/user/margins")
        equity = self._mapping(data.get("equity"), "margins.equity")
        available = self._mapping(equity.get("available"), "margins.equity.available")
        utilised = self._mapping(equity.get("utilised"), "margins.equity.utilised")
        cash = self._number(available.get("cash"))
        collateral = self._number(available.get("collateral"))
        return BrokerAccountSnapshot(
            snapshot_id=f"kite-account-{digest[:12]}",
            broker=self.broker,
            account_id_hash=self._account_hash,
            captured_at=captured,
            source_timestamp=captured,
            source_sequence=self._sequence,
            schema_version=_SCHEMA,
            payload_hash=digest,
            available_cash=cash,
            collateral=collateral,
            utilized_margin=self._number(utilised.get("debits")),
            available_margin=self._number(equity.get("net")),
            buying_power=self._number_or_none(equity.get("net")),
        )

    def positions(self) -> tuple[BrokerPositionSnapshot, ...]:
        data, digest, captured = self._json("/portfolio/positions")
        net = self._sequence_data(data.get("net"), "positions.net")
        rows: list[BrokerPositionSnapshot] = []
        for index, item in enumerate(net):
            mapping = self._map_item(item, captured)
            row_hash = self._row_hash(digest, index, item)
            rows.append(
                BrokerPositionSnapshot(
                    snapshot_id=f"kite-position-{row_hash[:12]}",
                    broker=self.broker,
                    account_id_hash=self._account_hash,
                    captured_at=captured,
                    source_timestamp=captured,
                    source_sequence=self._sequence,
                    schema_version=_SCHEMA,
                    payload_hash=row_hash,
                    broker_instrument_id=mapping.broker_instrument_id,
                    security_id=mapping.security_id,
                    exchange=mapping.exchange,
                    quantity=self._number(item.get("quantity")),
                    average_price=self._number(item.get("average_price")),
                    last_price=self._number_or_none(item.get("last_price")),
                    unrealized_pnl=self._number_or_none(item.get("pnl")),
                    product=str(item.get("product") or "unknown"),
                    accounting_semantics="KITE_PORTFOLIO_NET_PNL",
                )
            )
        return tuple(rows)

    def holdings(self) -> tuple[BrokerHoldingSnapshot, ...]:
        data, digest, captured = self._json("/portfolio/holdings")
        rows: list[BrokerHoldingSnapshot] = []
        for index, item in enumerate(self._sequence_data(data, "holdings")):
            mapping = self._map_item(item, captured)
            row_hash = self._row_hash(digest, index, item)
            rows.append(
                BrokerHoldingSnapshot(
                    snapshot_id=f"kite-holding-{row_hash[:12]}",
                    broker=self.broker,
                    account_id_hash=self._account_hash,
                    captured_at=captured,
                    source_timestamp=captured,
                    source_sequence=self._sequence,
                    schema_version=_SCHEMA,
                    payload_hash=row_hash,
                    broker_instrument_id=mapping.broker_instrument_id,
                    security_id=mapping.security_id,
                    exchange=mapping.exchange,
                    quantity=self._number(item.get("quantity")),
                    average_cost=self._number(item.get("average_price")),
                )
            )
        return tuple(rows)

    def margins(self) -> BrokerMarginSnapshot:
        account = self.account()
        return BrokerMarginSnapshot(
            snapshot_id=account.snapshot_id.replace("account", "margin"),
            broker=account.broker,
            account_id_hash=account.account_id_hash,
            captured_at=account.captured_at,
            source_timestamp=account.source_timestamp,
            source_sequence=account.source_sequence,
            schema_version=account.schema_version,
            payload_hash=account.payload_hash,
            utilized_margin=account.utilized_margin,
            available_margin=account.available_margin,
            collateral=account.collateral,
            settlement_semantics="KITE_USER_MARGINS_EQUITY",
        )

    def orders(self) -> tuple[BrokerOrderSnapshot, ...]:
        data, digest, captured = self._json("/orders")
        rows: list[BrokerOrderSnapshot] = []
        for index, item in enumerate(self._sequence_data(data, "orders")):
            mapping = self._map_item(item, captured)
            row_hash = self._row_hash(digest, index, item)
            rows.append(
                BrokerOrderSnapshot(
                    snapshot_id=f"kite-order-{row_hash[:12]}",
                    broker=self.broker,
                    account_id_hash=self._account_hash,
                    captured_at=captured,
                    source_timestamp=captured,
                    source_sequence=self._sequence,
                    schema_version=_SCHEMA,
                    payload_hash=row_hash,
                    broker_order_id=self._required_str(item, "order_id", "order"),
                    status=str(item.get("status") or "unknown"),
                    side=str(item.get("transaction_type") or "unknown"),
                    quantity=self._number(item.get("quantity")),
                    filled_quantity=self._number(item.get("filled_quantity")),
                    pending_quantity=self._number(item.get("pending_quantity")),
                    order_type=str(item.get("order_type") or "unknown"),
                    price=self._number_or_none(item.get("price")),
                    rejection_reason=str(item.get("status_message") or ""),
                    broker_instrument_id=mapping.broker_instrument_id,
                )
            )
        return tuple(rows)

    def fills(self) -> tuple[BrokerFillSnapshot, ...]:
        return self.trades()

    def trades(self) -> tuple[BrokerFillSnapshot, ...]:
        data, digest, captured = self._json("/trades")
        rows: list[BrokerFillSnapshot] = []
        for index, item in enumerate(self._sequence_data(data, "trades")):
            row_hash = self._row_hash(digest, index, item)
            rows.append(
                BrokerFillSnapshot(
                    snapshot_id=f"kite-trade-{row_hash[:12]}",
                    broker=self.broker,
                    account_id_hash=self._account_hash,
                    captured_at=captured,
                    source_timestamp=captured,
                    source_sequence=self._sequence,
                    schema_version=_SCHEMA,
                    payload_hash=row_hash,
                    broker_fill_id=self._required_str(item, "trade_id", "trade"),
                    broker_order_id=self._required_str(item, "order_id", "trade"),
                    quantity=self._number(item.get("quantity", item.get("filled"))),
                    price=self._number(item.get("average_price")),
                    exchange=str(item.get("exchange") or "UNKNOWN"),
                )
            )
        return tuple(rows)

    def instrument_metadata(self) -> tuple[InstrumentMapping, ...]:
        response = self._get("/instruments")
        captured = self._record_observation()
        try:
            text = response.body.decode("utf-8")
            rows = csv.DictReader(io.StringIO(text))
        except (UnicodeDecodeError, csv.Error) as exc:
            raise BrokerGatewayError(
                f"kite instruments schema invalid: {type(exc).__name__}"
            ) from None
        for row in rows:
            self._map_fields(
                exchange=str(row.get("exchange") or "UNKNOWN"),
                symbol=str(row.get("tradingsymbol") or "UNKNOWN"),
                token=str(row.get("instrument_token") or "UNKNOWN"),
                captured=captured,
                source="kite-instruments",
            )
        if not self._mappings:
            raise BrokerGatewayError("kite instruments response was empty or malformed")
        return tuple(sorted(self._mappings.values(), key=lambda item: item.broker_instrument_id))

    def session_status(self) -> Provenance:
        captured = self._last_observed_at or self._now()
        return Provenance(
            adapter_id=self.adapter_id,
            broker=self.broker,
            captured_at=captured,
            source_timestamp=captured,
            gateway_receipt_at=captured,
            source_sequence=self._sequence,
            schema_version=_SCHEMA,
            note="Kite REST has no envelope source timestamp; captured_at is gateway receipt time.",
        )

    def snapshot(self) -> GatewaySnapshotBundle:
        capture_started_at = datetime.now(tz=UTC)
        profile = self.profile()
        account = self.account()
        positions = self.positions()
        holdings = self.holdings()
        margins = self.margins()
        orders = self.orders()
        trades = self.trades()
        digest = sha256_bytes(
            "|".join(
                [
                    profile.payload_hash,
                    account.payload_hash,
                    *(item.payload_hash for item in positions),
                    *(item.payload_hash for item in holdings),
                    *(item.payload_hash for item in orders),
                    *(item.payload_hash for item in trades),
                ]
            ).encode()
        )
        return GatewaySnapshotBundle(
            bundle_id=f"kite-snapshot-{digest[:12]}",
            connection_id=f"kite-{self._account_hash}",
            adapter_id=self.adapter_id,
            provenance=self.session_status(),
            profile=profile,
            account=account,
            positions=positions,
            holdings=holdings,
            margins=margins,
            orders=orders,
            fills=trades,
            trades=trades,
            mappings=tuple(
                sorted(self._mappings.values(), key=lambda item: item.broker_instrument_id)
            ),
            payload_hash=digest,
            extras={"data_kind": "broker_observation", "read_only": True},
            capture_started_at=capture_started_at,
            capture_completed_at=datetime.now(tz=UTC),
        )

    def place_order(self, *_args: object, **_kwargs: object) -> None:
        raise BrokerWriteError("Kite read-only adapter cannot place orders")

    def cancel_order(self, *_args: object, **_kwargs: object) -> None:
        raise BrokerWriteError("Kite read-only adapter cannot cancel orders")

    def modify_order(self, *_args: object, **_kwargs: object) -> None:
        raise BrokerWriteError("Kite read-only adapter cannot modify orders")

    def _get(self, path: str) -> HttpResponse:
        if path not in {
            "/user/profile",
            "/user/margins",
            "/portfolio/holdings",
            "/portfolio/positions",
            "/orders",
            "/trades",
            "/instruments",
        }:
            raise BrokerWriteError("Kite read-only adapter rejected an unapproved endpoint")
        headers = {
            "X-Kite-Version": "3",
            "Authorization": f"token {self._config.api_key}:{self._config.access_token}",
        }
        for attempt in range(self._config.max_attempts):
            response = self._transport.get(path, headers, self._config.timeout_seconds)
            if response.status in {401, 403}:
                self._auth_state = "auth_expired" if response.status == 401 else "revoked"
                raise BrokerGatewayError(f"kite authentication rejected ({response.status})")
            if 200 <= response.status < 300:
                return response
            if response.status not in _RETRYABLE or attempt + 1 == self._config.max_attempts:
                self._auth_state = "error"
                raise BrokerGatewayError(f"kite read request failed ({response.status})")
            self._sleep(0.25 * (2**attempt))
        raise BrokerGatewayError("kite retry exhausted")

    def _json(self, path: str) -> tuple[dict[str, object], str, datetime]:
        response = self._get(path)
        digest = sha256_bytes(response.body)
        captured = self._record_observation()
        try:
            envelope = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BrokerGatewayError(
                f"kite response schema invalid: {type(exc).__name__}"
            ) from None
        if not isinstance(envelope, dict) or envelope.get("status") != "success":
            raise BrokerGatewayError("kite response status was not success")
        data = envelope.get("data")
        if not isinstance(data, (dict, list)):
            raise BrokerGatewayError("kite response data was missing or malformed")
        return {"_list": data} if isinstance(data, list) else data, digest, captured

    def _map_item(self, item: dict[str, object], captured: datetime) -> InstrumentMapping:
        return self._map_fields(
            exchange=str(item.get("exchange") or "UNKNOWN"),
            symbol=str(item.get("tradingsymbol") or "UNKNOWN"),
            token=str(item.get("instrument_token") or "UNKNOWN"),
            captured=captured,
            source="kite-account-payload",
        )

    def _map_fields(
        self, *, exchange: str, symbol: str, token: str, captured: datetime, source: str
    ) -> InstrumentMapping:
        broker_id = f"KITE:{exchange}:{token}"
        existing = self._mappings.get(broker_id)
        if existing is not None:
            return existing
        canonical = None if self._master is None else self._master.resolve_symbol(symbol, captured)
        matches_exchange = canonical is not None and canonical.exchange == exchange
        security_id = (
            canonical.security_id
            if canonical is not None and matches_exchange
            else f"UNMAPPED:{exchange}:{symbol}"
        )
        mapping = InstrumentMapping(
            broker_instrument_id=broker_id,
            security_id=security_id,
            exchange=exchange,
            trading_symbol=symbol,
            display_symbol=symbol,
            effective_from=captured,
            mapping_source=source if matches_exchange else f"{source}:unmapped",
            mapping_confidence="high" if matches_exchange else "unmapped",
            ambiguous=False,
        )
        self._mappings[broker_id] = mapping
        return mapping

    def _record_observation(self) -> datetime:
        captured = self._now()
        self._last_observed_at = captured
        self._sequence += 1
        return captured

    def _now(self) -> datetime:
        value = self._clock()
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)

    @staticmethod
    def _mapping(value: object, field: str) -> dict[str, object]:
        if not isinstance(value, dict):
            raise BrokerGatewayError(f"kite response partial or malformed: {field}")
        return value

    @classmethod
    def _sequence_data(cls, value: object, field: str) -> list[dict[str, object]]:
        if isinstance(value, dict) and "_list" in value:
            value = value["_list"]
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            raise BrokerGatewayError(f"kite response partial or malformed: {field}")
        return list(value)

    @staticmethod
    def _number(value: object) -> float:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        raise BrokerGatewayError("kite response partial or malformed: numeric field")

    @staticmethod
    def _number_or_none(value: object) -> float | None:
        if value is None:
            return None
        return KiteReadOnlyAdapter._number(value)

    @staticmethod
    def _required_str(value: dict[str, object], key: str, section: str) -> str:
        item = value.get(key)
        if not isinstance(item, str) or not item:
            raise BrokerGatewayError(f"kite response partial or malformed: {section}.{key}")
        return item

    @staticmethod
    def _string_tuple(value: object) -> tuple[str, ...]:
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            return ()
        return tuple(value)

    @staticmethod
    def _row_hash(digest: str, index: int, value: dict[str, object]) -> str:
        material = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
        return sha256_bytes(f"{digest}|{index}|{material}".encode())


def kite_credentials_configured() -> bool:
    """Safe availability check; it does not return or log any credential values."""

    return bool(os.getenv("KITE_API_KEY") and os.getenv("KITE_ACCESS_TOKEN"))
