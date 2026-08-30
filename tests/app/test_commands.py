from pathlib import Path

import pytest

from quantlab.app.commands import execute_momentum_backtest, request_live_trading
from quantlab.app.jobs import Job, JobStatus
from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import SafetyError


def test_backtest_command_writes_ledger(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    job = Job(
        job_id="t",
        type="backtest",
        status=JobStatus.RUNNING,
        created_at="t",
        parameters={"n_days": 80, "lookback": 20, "top_n": 2, "cost_bps": 10.0},
    )
    result = execute_momentum_backtest(job, ledger)
    assert ledger.exists()
    assert result["live_trading"] is False
    assert result["integrity"]["look_ahead_bias"] == "pass"
    assert result["n_rebalances"] > 10
    assert "sharpe" in result["metrics"]


def test_zero_cost_command_rejected(tmp_path: Path) -> None:
    job = Job(
        job_id="t",
        type="backtest",
        status=JobStatus.RUNNING,
        created_at="t",
        parameters={"cost_bps": 0.0},
    )
    with pytest.raises(ValueError):
        execute_momentum_backtest(job, tmp_path / "ledger.jsonl")


def test_spawned_backtest_writes_ledger(tmp_path: Path) -> None:
    from quantlab.app.worker import run_backtest_spawned

    job = Job(
        job_id="spawn1",
        type="backtest",
        status=JobStatus.RUNNING,
        created_at="t",
        parameters={"n_days": 80, "lookback": 20, "top_n": 2, "cost_bps": 10.0},
    )
    result = run_backtest_spawned(job, tmp_path / "ledger.jsonl")
    assert (tmp_path / "ledger.jsonl").exists()
    assert result["integrity"]["look_ahead_bias"] == "pass"
    assert result["n_rebalances"] > 10


def test_live_command_blocked() -> None:
    with pytest.raises(SafetyError):
        request_live_trading(LiveSafetyGates())
