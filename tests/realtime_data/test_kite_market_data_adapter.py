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
from quantlab.realtime_data.service import (
    fetch_kite_snapshot,
    inspect,
    list_snapshots,
    reset_for_tests,
    save_observed_snapshot,
    snapshot,
    source_status,
    start,
)

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


def test_desktop_capture_is_isolated_and_only_explicit_capture_is_saved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start()
    demo = snapshot()
    transport = _Transport({"status": "success", "data": {"NSE:INFY": _quote("NSE:INFY", 1500)}})
    adapter = KiteMarketDataAdapter(_config("NSE:INFY"), transport=transport, clock=lambda: _NOW)
    monkeypatch.setattr(KiteMarketDataAdapter, "from_environment", lambda: adapter)
    frozen = fetch_kite_snapshot()
    assert list_snapshots() == [demo.snapshot_id]
    assert source_status()["active_source"] != "kite-rest-quote-v3"
    assert frozen.extras["active_source"] == "kite-rest-quote-v3"
    assert frozen.extras["max_quote_age_seconds"] == 5
    assert frozen.live_trading is False
    assert len(transport.calls) == 1 and transport.calls[0][0].startswith("/quote?")
    assert adapter.source_health()["connected"] is False
    save_observed_snapshot(frozen)
    assert inspect("last") == frozen


@pytest.mark.parametrize("flag", ["LIVE_TRADING", "BROKER_WRITE_ENABLED"])
def test_desktop_capture_refuses_write_enabled_safety_state(
    flag: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(flag, "true")
    with pytest.raises(RealTimeDataError, match="refuses"):
        fetch_kite_snapshot()


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


def test_mixed_watchlist_preserves_listings_and_index_units_without_fake_depth() -> None:
    symbols = ["NSE:BEL", "BSE:BEL", "NSE:NIFTY 50", "BSE:SENSEX", "GLOBAL:US10YRYIELD"]
    data = {symbol: _quote(symbol, 380.5) for symbol in symbols[:2]}
    for symbol, value in zip(symbols[2:], (22617.0, 72640.24, 5.27), strict=True):
        data[symbol] = {"last_price": value, "timestamp": "2026-10-03 09:30:00"}
    transport = _Transport({"status": "success", "data": data})
    adapter = KiteMarketDataAdapter(
        _config(",".join(symbols)), transport=transport, clock=lambda: _NOW
    )
    adapter.connect()
    rows = adapter.poll()

    assert [row.security_id for row in rows] == symbols
    assert rows[0].venue == "NSE" and rows[1].venue == "BSE"
    assert rows[-1].venue == "GLOBAL" and rows[-1].price == 5.27
    assert all(row.quality is QualityStatus.VALID and not row.live_trading for row in rows)
    assert all(row.bid is None and row.ask is None and row.volume is None for row in rows[2:])
    assert "i=NSE%3ANIFTY+50" in transport.calls[0][0]
    assert "i=GLOBAL%3AUS10YRYIELD" in transport.calls[0][0]
    assert adapter.source_health()["coverage"] == 1.0


@pytest.mark.parametrize(
    ("symbols", "message"),
    [
        ("NSE:BEL,NSE:BEL", "duplicate"),
        (",".join(f"NSE:TEST{i}" for i in range(501)), "at most 500"),
    ],
)
def test_watchlist_rejects_duplicates_and_provider_limit_overflow(
    symbols: str, message: str
) -> None:
    with pytest.raises(RealTimeDataError, match=message):
        KiteMarketDataAdapter(_config(symbols), transport=_Transport({}), clock=lambda: _NOW)
