from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from quantlab.realtime_data.errors import RealTimeDataError
from quantlab.realtime_data.kite import (
    KiteHttpResponse,
    KiteMarketDataAdapter,
    KiteMarketDataConfig,
)
from quantlab.realtime_data.models import QualityStatus
from quantlab.realtime_data.service import reset_for_tests, snapshot, start

pytestmark = pytest.mark.realtime_data

_NOW = datetime(2026, 10, 3, 4, 0, tzinfo=UTC)


class _Transport:
    def __init__(self, payload: dict[str, object], *, status: int = 200) -> None:
        self.payload = payload
        self.status = status
        self.calls: list[tuple[str, dict[str, str]]] = []

    def get(self, path: str, headers: dict[str, str], timeout_seconds: float) -> KiteHttpResponse:
        del timeout_seconds
        self.calls.append((path, headers))
        return KiteHttpResponse(status=self.status, body=json.dumps(self.payload).encode())


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_for_tests()


def _config(symbols: str = "NSE:INFY,NSE:TCS") -> KiteMarketDataConfig:
    fixture_auth = ("test-key", "test-token")
    return KiteMarketDataConfig(
        api_key=fixture_auth[0],
        access_token=fixture_auth[1],
        symbols=symbols,
    )


def _quote(symbol: str, price: float) -> dict[str, object]:
    return {
        "instrument_token": 408065 if symbol == "NSE:INFY" else 2953217,
        "last_price": price,
        "last_quantity": 10,
        "volume": 1000,
        "timestamp": "2026-10-03 09:30:00",
        "depth": {
            "buy": [{"price": price - 0.05, "quantity": 5}],
            "sell": [{"price": price + 0.05, "quantity": 5}],
        },
    }


def test_kite_quote_adapter_uses_read_only_quote_path_and_freezes_provenance() -> None:
    transport = _Transport(
        {
            "status": "success",
            "data": {
                "NSE:INFY": _quote("NSE:INFY", 1500.0),
                "NSE:TCS": _quote("NSE:TCS", 3500.0),
            },
        }
    )
    adapter = KiteMarketDataAdapter(_config(), transport=transport, clock=lambda: _NOW)
    start(adapter=adapter)
    frozen = snapshot(as_of=_NOW)

    assert frozen.n_names == 2
    assert frozen.quality is QualityStatus.VALID
    assert frozen.extras["active_source"] == "kite-rest-quote-v3"
    assert frozen.extras["source_manifest"] == "production-observe-only:kite-rest-quote-v3"
    assert all(row.live_trading is False for row in frozen.observations)
    assert transport.calls[0][0] == "/quote?i=NSE%3AINFY&i=NSE%3ATCS"
    assert transport.calls[0][1]["X-Kite-Version"] == "3"
    assert transport.calls[0][1]["Authorization"] == "token test-key:test-token"


def test_missing_quote_timestamp_and_instrument_degrade_never_upgrade_quality() -> None:
    row = _quote("NSE:INFY", 1500.0)
    row.pop("timestamp")
    adapter = KiteMarketDataAdapter(
        _config(),
        transport=_Transport({"status": "success", "data": {"NSE:INFY": row}}),
        clock=lambda: _NOW,
    )
    start(adapter=adapter)
    frozen = snapshot(as_of=_NOW)

    assert frozen.quality is QualityStatus.DEGRADED
    assert frozen.observations[0].exchange_time is None
    assert "missing_configured_instrument" in frozen.extras["quality_faults"]


def test_old_quote_and_zero_depth_are_stale_not_a_false_crossed_market_fault() -> None:
    row = _quote("NSE:INFY", 1500.0)
    row["timestamp"] = "2026-10-01 09:30:00"
    row["depth"] = {
        "buy": [{"price": 0.0, "quantity": 0}],
        "sell": [{"price": 0.0, "quantity": 0}],
    }
    adapter = KiteMarketDataAdapter(
        _config("NSE:INFY"),
        transport=_Transport({"status": "success", "data": {"NSE:INFY": row}}),
        clock=lambda: _NOW,
    )
    start(adapter=adapter)
    frozen = snapshot()

    assert frozen.as_of == _NOW
    assert frozen.quality is QualityStatus.STALE
    assert frozen.observations[0].bid is None
    assert frozen.observations[0].ask is None
    assert "crossed_or_locked_quote" not in frozen.extras["quality_faults"]


def test_kite_adapter_rejects_non_successful_response_without_exposing_body() -> None:
    adapter = KiteMarketDataAdapter(
        _config("NSE:INFY"),
        transport=_Transport({"status": "error", "message": "secret-never-echoed"}, status=403),
        clock=lambda: _NOW,
    )
    adapter.connect()
    with pytest.raises(RealTimeDataError, match="authentication rejected"):
        adapter.poll()


def test_kite_adapter_requires_explicit_exchange_scoped_symbols() -> None:
    with pytest.raises(RealTimeDataError, match="EXCHANGE:SYMBOL"):
        KiteMarketDataAdapter(_config("INFY"), transport=_Transport({}), clock=lambda: _NOW)
