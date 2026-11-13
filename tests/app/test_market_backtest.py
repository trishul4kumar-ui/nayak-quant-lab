from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from quantlab.agents.repository import AgentRepository
from quantlab.app.jobs import Job, JobStatus
from quantlab.app.market_backtest import (
    FrozenMarketHistory,
    MarketBacktestParameters,
    calculate_market_backtest,
    execute_market_backtest,
    freeze_history,
    verify_frozen_market_result,
)
from quantlab.models.registry import ExperimentLedger
from quantlab.realtime_data.candles import Candle, CandleSeries


def parameters(**changes: object) -> MarketBacktestParameters:
    return MarketBacktestParameters.model_validate(
        {"instrument": "BSE:BEL", "lookback": 5, **changes}
    )


def sample_series(params: MarketBacktestParameters, *, now: datetime | None = None) -> CandleSeries:
    now = now or datetime.now(UTC)
    start = (now - timedelta(days=15)).replace(hour=0, minute=0, second=0, microsecond=0)
    candles = tuple(
        Candle(
            start + timedelta(days=index),
            100 + index * 2,
            105 + index * 2,
            95 + index * 2,
            103 + index * 2,
            1000.0,
        )
        for index in range(12)
    )
    return CandleSeries(params.request(), candles, now)


def test_real_history_next_open_costs_and_binding() -> None:
    params = parameters()
    series = sample_series(params)
    frozen = freeze_history(series, params, now=series.fetched_at)
    result = calculate_market_backtest(frozen, params)
    assert result["data_kind"] == "REAL"
    assert result["source"] == "kite-historical-v3"
    assert result["history_hash"] == frozen.content_hash
    assert result["equity_curve"][0] == 100000
    first = result["fills"][0]
    assert first["signal_bar"] == series.candles[4].time.isoformat()
    assert first["fill_bar"] == series.candles[5].time.isoformat()
    assert first["price"] == pytest.approx(series.candles[5].open * 1.0005)
    assert first["fee"] > 0
    assert result["metrics"]["cost_drag"] > 0
    assert result["live_trading"] is False
    assert result["gate_outcome"] == "NOT_TESTED"
    assert all(fill["signal_bar"] < fill["fill_bar"] for fill in result["fills"])


def test_future_tail_cannot_change_earlier_equity() -> None:
    params = parameters()
    series = sample_series(params)
    changed = replace(series.candles[-1], open=300.0, high=310.0, low=290.0, close=305.0)
    other = replace(series, candles=(*series.candles[:-1], changed))
    first = calculate_market_backtest(freeze_history(series, params, now=series.fetched_at), params)
    second = calculate_market_backtest(freeze_history(other, params, now=series.fetched_at), params)
    assert first["equity_curve"][:-1] == second["equity_curve"][:-1]
    assert first["config_hash"] != second["config_hash"]


def test_forming_bar_excluded_not_used() -> None:
    params = parameters()
    series = sample_series(params)
    forming = Candle(
        series.fetched_at.replace(hour=0, minute=0, second=0, microsecond=0),
        1000,
        1010,
        990,
        1005,
        2000,
    )
    frozen = freeze_history(
        replace(series, candles=(*series.candles, forming)), params, now=series.fetched_at
    )
    assert frozen.excluded_forming_bars == 1
    assert len(frozen.candles) == len(series.candles)


@pytest.mark.parametrize(
    "fault", ["source", "instrument", "interval", "stale", "future", "short", "duplicate", "ohlc"]
)
def test_rejects_untrusted_or_insufficient_history(fault: str) -> None:
    params = parameters()
    series = sample_series(params)
    if fault == "source":
        series = replace(series, source="synthetic")
    elif fault == "instrument":
        series = replace(series, request=parameters(instrument="NSE:INFY").request())
    elif fault == "interval":
        series = replace(series, request=parameters(interval="minute", days=5).request())
    elif fault == "stale":
        series = replace(series, fetched_at=series.fetched_at - timedelta(minutes=3))
    elif fault == "future":
        series = replace(series, fetched_at=series.fetched_at + timedelta(minutes=3))
    elif fault == "short":
        series = replace(series, candles=series.candles[:5])
    elif fault == "duplicate":
        series = replace(series, candles=(series.candles[0], *series.candles))
    else:
        series = replace(series, candles=(replace(series.candles[0], high=1), *series.candles[1:]))
    with pytest.raises(ValueError):
        freeze_history(series, params, now=datetime.now(UTC))


@pytest.mark.parametrize(
    "values",
    [
        {"days": True},
        {"interval": "minute", "days": 366},
        {"cost_bps": 0},
        {"slippage_bps": -1},
        {"instrument": "NFO:FUT"},
        {"data_kind": "SYNTHETIC"},
        {"lookback": 100},
        {"shell": "cmd"},
    ],
)
def test_market_parameters_are_bounded(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        parameters(**values)


def test_persisted_result_provenance_and_tampering(tmp_path: Path) -> None:
    params = parameters()
    job = Job(
        "market-test",
        "market_backtest",
        JobStatus.RUNNING,
        "now",
        parameters=params.model_dump(mode="json"),
    )
    database = tmp_path / "agent.sqlite"
    ledger = tmp_path / "ledger.jsonl"
    result = execute_market_backtest(
        job, ledger, tmp_path / "artifacts", database, fetch=lambda _: sample_series(params)
    )
    repository = AgentRepository(database)
    try:
        history = verify_frozen_market_result(repository, result, params)
        assert isinstance(history, FrozenMarketHistory)
        run = ExperimentLedger(ledger).get(result["experiment_id"])
        assert run is not None and run.data_kind == "real" and run.status.value == "completed"
        assert run.config_hash == result["config_hash"]
        assert run.dataset_id == history.content_hash
        assert run.gate_outcome == "NOT_TESTED"
        bad = {**result, "equity_curve": [100000, 999999]}
        with pytest.raises(ValueError, match="ARTIFACT_BINDING"):
            verify_frozen_market_result(repository, bad, params)
        with pytest.raises(ValueError, match="ARTIFACT_BINDING"):
            verify_frozen_market_result(repository, result, parameters(cost_bps=20.0))
    finally:
        repository.close()


def test_capture_failure_never_runs_synthetic_or_creates_ledger(tmp_path: Path) -> None:
    params = parameters()
    job = Job(
        "market-test",
        "market_backtest",
        JobStatus.RUNNING,
        "now",
        parameters=params.model_dump(mode="json"),
    )

    def missing(_request):
        raise ValueError("BROKER_HISTORY_UNAVAILABLE")

    with pytest.raises(ValueError, match="BROKER_HISTORY_UNAVAILABLE"):
        execute_market_backtest(
            job,
            tmp_path / "ledger.jsonl",
            tmp_path / "artifacts",
            tmp_path / "agent.sqlite",
            fetch=missing,
        )
    assert not (tmp_path / "ledger.jsonl").exists()


def test_cancel_before_capture_and_during_calculation(tmp_path: Path) -> None:
    params = parameters()
    job = Job(
        "cancel-test",
        "market_backtest",
        JobStatus.RUNNING,
        "now",
        parameters=params.model_dump(mode="json"),
    )
    job.cancel_event.set()
    with pytest.raises(ValueError, match="cancelled"):
        execute_market_backtest(
            job,
            tmp_path / "ledger.jsonl",
            tmp_path / "artifacts",
            tmp_path / "agent.sqlite",
            fetch=lambda _: pytest.fail("capture should not run"),
        )
    series = sample_series(params)
    with pytest.raises(ValueError, match="cancelled"):
        calculate_market_backtest(
            freeze_history(series, params, now=series.fetched_at), params, cancelled=lambda: True
        )
