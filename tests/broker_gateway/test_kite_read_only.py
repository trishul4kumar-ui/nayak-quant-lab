from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from quantlab.broker_gateway.errors import BrokerGatewayError, BrokerWriteError
from quantlab.broker_gateway.kite import (
    HttpResponse,
    KiteReadOnlyAdapter,
    KiteReadOnlyConfig,
)

pytestmark = pytest.mark.broker_gateway


class FakeKiteTransport:
    def __init__(self, responses: dict[str, HttpResponse]) -> None:
        self.responses = responses
        self.paths: list[str] = []
        self.headers: list[dict[str, str]] = []

    def get(self, path: str, headers: dict[str, str], timeout_seconds: float) -> HttpResponse:
        del timeout_seconds
        self.paths.append(path)
        self.headers.append(dict(headers))
        return self.responses[path]


def _response(data: object, *, status: int = 200) -> HttpResponse:
    return HttpResponse(status, json.dumps({"status": "success", "data": data}).encode(), {})


def _adapter(transport: FakeKiteTransport) -> KiteReadOnlyAdapter:
    fixture_auth = ("test-key", "test-token")
    return KiteReadOnlyAdapter(
        KiteReadOnlyConfig(api_key=fixture_auth[0], access_token=fixture_auth[1]),
        transport=transport,
        clock=lambda: datetime(2026, 10, 2, tzinfo=UTC),
        sleeper=lambda _: None,
    )


def _normal_transport() -> FakeKiteTransport:
    return FakeKiteTransport(
        {
            "/user/profile": _response(
                {
                    "user_id": "AB1234",
                    "exchanges": ["NSE"],
                    "products": ["CNC"],
                    "order_types": ["LIMIT"],
                }
            ),
            "/user/margins": _response(
                {
                    "equity": {
                        "net": 1000,
                        "available": {"cash": 900, "collateral": 10},
                        "utilised": {"debits": 110},
                    }
                }
            ),
            "/portfolio/positions": _response(
                {
                    "net": [
                        {
                            "exchange": "NSE",
                            "tradingsymbol": "INFY",
                            "instrument_token": 408065,
                            "quantity": 2,
                            "average_price": 1500,
                            "last_price": 1510,
                            "pnl": 20,
                            "product": "CNC",
                        }
                    ]
                }
            ),
            "/portfolio/holdings": _response(
                [
                    {
                        "exchange": "NSE",
                        "tradingsymbol": "INFY",
                        "instrument_token": 408065,
                        "quantity": 2,
                        "average_price": 1500,
                    }
                ]
            ),
            "/orders": _response(
                [
                    {
                        "order_id": "O1",
                        "exchange": "NSE",
                        "tradingsymbol": "INFY",
                        "instrument_token": 408065,
                        "status": "COMPLETE",
                        "transaction_type": "BUY",
                        "quantity": 2,
                        "filled_quantity": 2,
                        "pending_quantity": 0,
                        "order_type": "LIMIT",
                        "price": 1500,
                    }
                ]
            ),
            "/trades": _response(
                [
                    {
                        "trade_id": "T1",
                        "order_id": "O1",
                        "exchange": "NSE",
                        "quantity": 2,
                        "average_price": 1500,
                    }
                ]
            ),
        }
    )


def test_kite_snapshot_uses_only_documented_read_endpoints_and_redacts_credentials() -> None:
    transport = _normal_transport()
    adapter = _adapter(transport)

    assert adapter.connect().healthy is True
    bundle = adapter.snapshot()

    assert set(transport.paths) == {
        "/user/profile",
        "/user/margins",
        "/portfolio/positions",
        "/portfolio/holdings",
        "/orders",
        "/trades",
    }
    assert bundle.profile.account_id_hash != "AB1234"
    assert bundle.positions[0].security_id == "UNMAPPED:NSE:INFY"
    assert "test-key" not in bundle.model_dump_json()
    assert "test-token" not in bundle.model_dump_json()


def test_kite_auth_failure_fails_closed_without_secret_echo() -> None:
    transport = FakeKiteTransport({"/user/profile": HttpResponse(401, b"denied", {})})
    adapter = _adapter(transport)

    with pytest.raises(BrokerGatewayError, match="authentication rejected") as exc:
        adapter.connect()

    assert adapter.auth_state == "auth_expired"
    assert "test-key" not in str(exc.value)
    assert "test-token" not in str(exc.value)


def test_kite_adapter_rejects_every_write_operation() -> None:
    adapter = _adapter(_normal_transport())
    for operation in (adapter.place_order, adapter.modify_order, adapter.cancel_order):
        with pytest.raises(BrokerWriteError):
            operation("anything")
