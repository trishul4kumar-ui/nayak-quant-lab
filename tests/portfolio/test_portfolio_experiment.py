"""Seed portfolio experiments use the existing engine and Prompt 05 gate."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.alpha.ensemble import get_ensemble
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import Instrument
from quantlab.portfolio.experiment import run_named_portfolio_experiment, run_portfolio_experiment
from quantlab.portfolio.spec import get_portfolio_model
from quantlab.research.gate import GateOutcome


@pytest.mark.portfolio
def test_synthetic_portfolio_cannot_promote(tmp_path: Path) -> None:
    report, run, result = run_named_portfolio_experiment(
        "mom20_topn",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        append=True,
    )
    assert report.gate.outcome is GateOutcome.WARN
    assert report.gate.outcome is not GateOutcome.RESEARCH_CANDIDATE
    assert report.data_kind == "synthetic"
    assert report.integrity["synthetic_data"] == "warn"
    assert report.integrity["future_covariance"] == "pass"
    assert report.integrity["survivorship_bias"] == "not_tested"
    assert not report.infeasible
    assert result is not None
    assert result.n_rebalances > 10
    assert run.portfolio_id == "mom20_topn"
    assert run.ensemble_id == "mom20"
    assert (tmp_path / "ledger.jsonl").exists()


@pytest.mark.portfolio
def test_equal_weight_ensemble_portfolio_runs() -> None:
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
    report, _, result = run_portfolio_experiment(
        bars=bars,
        instruments=instruments,
        model=get_portfolio_model("mom_5_20_ew"),
        ensemble=get_ensemble("mom_5_20"),
        data_kind="synthetic",
        append=False,
    )
    assert report.gate.outcome is GateOutcome.WARN
    assert result is not None
    assert report.last_diagnostics is not None
    assert report.last_diagnostics.gross == pytest.approx(1.0, abs=1e-6)


@pytest.mark.portfolio
def test_long_short_seed_allows_shorts() -> None:
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
    report, _, result = run_portfolio_experiment(
        bars=bars,
        instruments=instruments,
        model=get_portfolio_model("mom20_ls"),
        ensemble=get_ensemble("mom20"),
        data_kind="synthetic",
        append=False,
    )
    assert result is not None
    assert report.last_diagnostics is not None
    assert report.last_diagnostics.gross == pytest.approx(1.0, abs=1e-6)
    assert abs(report.last_diagnostics.net) < 0.05
