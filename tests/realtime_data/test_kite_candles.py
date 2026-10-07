from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from quantlab.realtime_data.candles import ChartRequest, KiteCandleClient
from quantlab.realtime_data.errors import RealTimeDataError
from quantlab.realtime_data.kite import KiteHttpResponse, KiteMarketDataConfig

NOW = datetime(2026, 10, 7, 4, 30, 30, tzinfo=UTC)


class Transport:
    def __init__(self, candles: list[object], status: int = 200) -> None:
        self.candles, self.status = candles, status
        self.paths: list[str] = []

    def get(self, path: str, headers: dict[str, str], timeout_seconds: float) -> KiteHttpResponse:
        del headers, timeout_seconds
        self.paths.append(path)
        data = (
            {"NSE:INFY": {"instrument_token": 408065}}
            if path.startswith("/quote?")
            else {"candles": self.candles}
        )
        return KiteHttpResponse(
            self.status, json.dumps({"status": "success", "data": data}).encode()
        )


def client(transport: Transport) -> KiteCandleClient:
    return KiteCandleClient(
        transport=transport,
        clock=lambda: NOW,
        config=lambda: KiteMarketDataConfig(
            _env_file=None, api_key="fixture", access_token="fixture", symbols="NSE:INFY"
        ),
    )


def candle(time: str = "2026-10-07T10:00:00+05:30") -> list[object]:
    return [time, 100, 102, 99, 101, 50]


def test_real_provider_candle_shape_token_resolution_and_bounded_get_paths() -> None:
    transport = Transport([candle()])
    source = client(transport)
    result = source.fetch(ChartRequest("NSE:INFY", "minute", 1))
    assert result.candles[0].close == 101
    assert result.candles[0].time == datetime(2026, 10, 7, 4, 30, tzinfo=UTC)
    assert result.is_forming(result.candles[0])
    assert result.source == "kite-historical-v3"
    assert transport.paths[0] == "/quote?i=NSE%3AINFY"
    assert transport.paths[1].startswith("/instruments/historical/408065/minute?")
    assert "continuous=0" in transport.paths[1] and "oi=0" in transport.paths[1]
    source.fetch(ChartRequest("NSE:INFY", "minute", 1))
    assert len(transport.paths) == 3  # token reused only in this client/day


@pytest.mark.parametrize(
    "raw",
    [
        ["2026-10-07T10:00:00", 100, 102, 99, 101, 50],
        ["not-a-time", 100, 102, 99, 101, 50],
        ["2026-10-07T10:00:00+05:30", 100, 98, 99, 101, 50],
        ["2026-10-07T10:00:00+05:30", float("nan"), 102, 99, 101, 50],
        ["2026-10-07T10:00:00+05:30", True, 102, 99, 101, 50],
        ["2026-10-07T10:00:00+05:30", 100, 102, 99, 101, -1],
    ],
)
def test_malformed_candles_fail_without_manufacturing_ohlc(raw: list[object]) -> None:
    with pytest.raises(RealTimeDataError, match="invalid"):
        client(Transport([raw])).fetch(ChartRequest("NSE:INFY"))


@pytest.mark.parametrize(
    "rows",
    [
        [candle(), candle()],
        [candle("2026-10-07T10:01:00+05:30")],
        [candle("2026-10-06T10:00:00+05:30")],
    ],
)
def test_duplicate_future_or_out_of_range_candles_fail(rows: list[object]) -> None:
    with pytest.raises(RealTimeDataError):
        client(Transport(rows)).fetch(ChartRequest("NSE:INFY", days=1))


@pytest.mark.parametrize(
    "chart_request",
    [
        ChartRequest("NSE:OTHER"),
        ChartRequest("NSE:INFY", "10second"),
        ChartRequest("NSE:INFY", days=366),
    ],
)
def test_configured_identity_interval_and_range_are_required(chart_request: ChartRequest) -> None:
    transport = Transport([])
    with pytest.raises(RealTimeDataError):
        client(transport).fetch(chart_request)
    assert not transport.paths


@pytest.mark.parametrize("flag", ["LIVE_TRADING", "BROKER_WRITE_ENABLED"])
def test_candles_refuse_write_enabled_state(flag: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(flag, "true")
    transport = Transport([])
    with pytest.raises(RealTimeDataError, match="refuses"):
        client(transport).fetch(ChartRequest("NSE:INFY"))
    assert not transport.paths


def test_empty_history_is_explicit_and_auth_body_is_redacted() -> None:
    assert client(Transport([])).fetch(ChartRequest("NSE:INFY")).candles == ()
    with pytest.raises(RealTimeDataError, match="authentication rejected"):
        client(Transport(["secret"], 403)).fetch(ChartRequest("NSE:INFY"))
