"""Ensemble experiments use the Prompt 05 gate. Leaks FAIL. Synthetic cannot promote."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import Instrument
from quantlab.ensemble.definition import EnsembleLeakFlags
from quantlab.ensemble.experiment import (
    compare_static_vs_adaptive,
    run_ensemble_comparison,
    run_ensemble_experiment,
    run_named_ensemble_experiment,
)
from quantlab.ensemble.registry import get_ensemble
from quantlab.research.gate import GateOutcome


def _frame() -> tuple[dict, list[Instrument]]:
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
    return bars, instruments


@pytest.mark.ensemble
def test_synthetic_ensemble_cannot_promote(tmp_path: Path) -> None:
    report, run, wf = run_named_ensemble_experiment(
        "ew_mom_5_20",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        append=True,
    )
    assert report.gate.outcome is GateOutcome.WARN
    assert report.gate.outcome is not GateOutcome.RESEARCH_CANDIDATE
    assert report.data_kind == "synthetic"
    assert report.integrity["future_ensemble_weight"] == "pass"
    assert report.integrity["stacking_leak"] == "pass"
    assert wf.n_scored > 0
    assert run.selection_stage == "meta_ensemble"
    assert run.weighting_policy == "equal"
    assert (tmp_path / "artifacts" / run.id / "walkforward.json").is_file()


@pytest.mark.ensemble
def test_future_weights_fail() -> None:
    bars, instruments = _frame()
    report, run, _wf = run_ensemble_experiment(
        bars=bars,
        instruments=instruments,
        definition=get_ensemble("static_ic_mom"),
        data_kind="synthetic",
        leaks=EnsembleLeakFlags(future_weights=True),
        append=False,
    )
    assert report.integrity["future_ensemble_weight"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT
    assert run.status.value == "failed"


@pytest.mark.ensemble
def test_future_correlation_fail() -> None:
    bars, instruments = _frame()
    report, _run, _wf = run_ensemble_experiment(
        bars=bars,
        instruments=instruments,
        definition=get_ensemble("corr_mom"),
        data_kind="synthetic",
        leaks=EnsembleLeakFlags(future_correlation=True),
        append=False,
    )
    assert report.integrity["future_correlation"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT


@pytest.mark.ensemble
def test_stacking_leak_fails() -> None:
    bars, instruments = _frame()
    report, _run, _wf = run_ensemble_experiment(
        bars=bars,
        instruments=instruments,
        definition=get_ensemble("ridge_stack_mom"),
        data_kind="synthetic",
        leaks=EnsembleLeakFlags(stacking_leak=True),
        append=False,
    )
    assert report.integrity["stacking_leak"] == "fail"
    assert report.integrity["future_stacking_prediction"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT


@pytest.mark.ensemble
def test_holdout_contamination_fails() -> None:
    bars, instruments = _frame()
    dates = sorted({b.pit.event_time for series in bars.values() for b in series})
    holdout = dates[(len(dates) * 2) // 3]
    report, _run, _wf = run_ensemble_experiment(
        bars=bars,
        instruments=instruments,
        definition=get_ensemble("roll_ic_mom"),
        data_kind="synthetic",
        leaks=EnsembleLeakFlags(holdout_contaminated=True),
        holdout_start=holdout,
        append=False,
    )
    assert report.integrity["holdout_contamination"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT


@pytest.mark.ensemble
def test_family_comparison_records_all_candidates() -> None:
    bars, instruments = _frame()
    report = run_ensemble_comparison(
        bars=bars,
        instruments=instruments,
        ensemble_ids=["ew_mom_5_20", "static_ic_mom", "corr_mom", "ridge_stack_mom"],
        append=False,
    )
    assert report.family_size == 4
    assert len(report.rows) == 4
    assert report.gate_outcome == "warn"
    assert "not market evidence" in report.note.lower()


@pytest.mark.ensemble
def test_search_truncated_flag() -> None:
    bars, instruments = _frame()
    report = run_ensemble_comparison(
        bars=bars,
        instruments=instruments,
        ensemble_ids=["ew_mom_5_20", "static_ic_mom", "corr_mom"],
        max_trials=2,
        append=False,
    )
    assert report.search_truncated is True
    assert len(report.rows) == 2
    assert report.family_size == 3


@pytest.mark.ensemble
def test_adaptive_integration_does_not_reimplement() -> None:
    bars, instruments = _frame()
    payload = compare_static_vs_adaptive(bars=bars, instruments=instruments)
    assert payload["static_ensemble_id"] == "ew_mom_5_20"
    assert payload["adaptive_model_id"] == "ensemble_ic_mom"
    assert "not reimplemented" in payload["note"]
