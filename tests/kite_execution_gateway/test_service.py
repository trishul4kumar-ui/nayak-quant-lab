from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from quantlab.broker_gateway.secrets import account_id_hash
from quantlab.kite_execution_gateway.config import KiteExecutionGatewayConfig
from quantlab.kite_execution_gateway.models import (
    ManualLimitOrder,
    ManualOrderSubmission,
    SubmissionState,
)
from quantlab.kite_execution_gateway.service import (
    GatewayError,
    GatewayTimeout,
    HttpResponse,
    SecureKiteExecutionGateway,
    _totp,
)


class FakeTransport:
    def __init__(self, *, user_id: str = "AB1234", timeout: bool = False) -> None:
        self.user_id = user_id
        self.timeout = timeout
        self.calls: list[tuple[str, str]] = []

    def request(
        self, method: str, path: str, headers: dict[str, str], body: bytes = b""
    ) -> HttpResponse:
        del headers, body
        self.calls.append((method, path))
        if path == "/session/token":
            return _response({"access_token": "test-access-token", "user_id": self.user_id})
        if self.timeout:
            raise GatewayTimeout("test timeout")
        return _response({"order_id": "250101000001"})


def _response(data: dict[str, object]) -> HttpResponse:
    return HttpResponse(200, json.dumps({"status": "success", "data": data}).encode())


def _config(tmp_path: Path, *, enabled: bool = True) -> KiteExecutionGatewayConfig:
    # Explicit test-only fixture, not deployed credentials.
    fixture_auth = ("test-key", "test-secret", "JBSWY3DPEHPK3PXP")
    return KiteExecutionGatewayConfig(
        api_key=fixture_auth[0],
        api_secret=fixture_auth[1],
        desktop_client_token="desktop-token",
        operator_totp_secret=fixture_auth[2],
        expected_account_fingerprint=account_id_hash("AB1234"),
        allowed_symbols=frozenset({"NSE:INFY"}),
        max_notional=100_000.0,
        redirect_url="https://gateway.example.test/v1/kite/callback",
        journal_path=tmp_path / "gateway.sqlite",
        execution_enabled=enabled,
    )


def _order(now: datetime) -> ManualLimitOrder:
    return ManualLimitOrder(
        client_request_id="desktop-request-1",
        idempotency_key="desktop-idempotency-key-1",
        account_fingerprint=account_id_hash("AB1234"),
        exchange="NSE",
        tradingsymbol="INFY",
        transaction_type="BUY",
        quantity=2,
        product="CNC",
        order_type="LIMIT",
        price=1500.0,
        validity="DAY",
        created_at=now,
        expires_at=now + timedelta(minutes=2),
    )


def _gateway(
    tmp_path: Path, transport: FakeTransport, *, enabled: bool = True
) -> SecureKiteExecutionGateway:
    now = datetime(2026, 10, 4, 9, 30, tzinfo=UTC)
    return SecureKiteExecutionGateway(
        _config(tmp_path, enabled=enabled), transport=transport, clock=lambda: now
    )


def _authenticate(gateway: SecureKiteExecutionGateway) -> None:
    gateway.authenticate_request_token("short-lived-request-token")


def test_manual_limit_order_requires_exact_confirmation_and_is_submitted_once(
    tmp_path: Path,
) -> None:
    transport = FakeTransport()
    gateway = _gateway(tmp_path, transport)
    _authenticate(gateway)
    now = datetime(2026, 10, 4, 9, 30, tzinfo=UTC)
    order = _order(now)
    preview = gateway.preview(order)
    result = gateway.submit(
        ManualOrderSubmission(
            order=order,
            intent_hash=preview.intent_hash,
            confirmation_text=preview.confirmation_text,
            totp_code=_totp("JBSWY3DPEHPK3PXP", int(now.timestamp() // 30)),
        )
    )

    assert result.state is SubmissionState.ACKNOWLEDGED
    assert result.broker_order_id == "250101000001"
    assert transport.calls == [("POST", "/session/token"), ("POST", "/orders/regular")]
    assert (
        gateway.submit(
            ManualOrderSubmission(
                order=order,
                intent_hash=preview.intent_hash,
                confirmation_text=preview.confirmation_text,
                totp_code=_totp("JBSWY3DPEHPK3PXP", int(now.timestamp() // 30)),
            )
        )
        == result
    )
    assert len(transport.calls) == 2


def test_gateway_rejects_disabled_execution_before_broker_order_call(tmp_path: Path) -> None:
    transport = FakeTransport()
    gateway = _gateway(tmp_path, transport, enabled=False)
    _authenticate(gateway)
    now = datetime(2026, 10, 4, 9, 30, tzinfo=UTC)
    order = _order(now)
    preview = gateway.preview(order)
    with pytest.raises(GatewayError, match="disabled"):
        gateway.submit(
            ManualOrderSubmission(
                order=order,
                intent_hash=preview.intent_hash,
                confirmation_text=preview.confirmation_text,
                totp_code=_totp("JBSWY3DPEHPK3PXP", int(now.timestamp() // 30)),
            )
        )
    assert transport.calls == [("POST", "/session/token")]


def test_gateway_turns_timeout_into_unknown_and_never_retries(tmp_path: Path) -> None:
    transport = FakeTransport(timeout=True)
    gateway = _gateway(tmp_path, transport)
    _authenticate(gateway)
    now = datetime(2026, 10, 4, 9, 30, tzinfo=UTC)
    order = _order(now)
    preview = gateway.preview(order)
    request = ManualOrderSubmission(
        order=order,
        intent_hash=preview.intent_hash,
        confirmation_text=preview.confirmation_text,
        totp_code=_totp("JBSWY3DPEHPK3PXP", int(now.timestamp() // 30)),
    )
    result = gateway.submit(request)
    assert result.state is SubmissionState.SUBMISSION_UNKNOWN
    assert gateway.submit(request) == result
    assert transport.calls == [("POST", "/session/token"), ("POST", "/orders/regular")]


def test_gateway_rejects_outside_allowlist_and_market_order(tmp_path: Path) -> None:
    gateway = _gateway(tmp_path, FakeTransport())
    now = datetime(2026, 10, 4, 9, 30, tzinfo=UTC)
    with pytest.raises(GatewayError, match="allowlist"):
        gateway.preview(_order(now).model_copy(update={"tradingsymbol": "TCS"}))
    with pytest.raises(GatewayError, match="NSE CNC LIMIT"):
        gateway.preview(_order(now).model_copy(update={"order_type": "MARKET"}))
