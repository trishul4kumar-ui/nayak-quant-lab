"""Adaptive experiments use the Prompt 05 gate. Leaks FAIL. Synthetic cannot promote."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.adaptive.experiment import (
    run_adaptive_comparison,
    run_adaptive_experiment,
    run_named_adaptive_experiment,
)
from quantlab.adaptive.registry import get_adaptive_model
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import Instrument
from quantlab.research.gate import GateOutcome


@pytest.mark.adaptive
def test_synthetic_adaptive_cannot_promote(tmp_path: Path) -> None:
    report, run, preq = run_named_adaptive_experiment(
        "static_mom20",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        append=True,
    )
    assert report.gate.outcome is GateOutcome.WARN
    assert report.gate.outcome is not GateOutcome.RESEARCH_CANDIDATE
    assert report.data_kind == "synthetic"
    assert report.integrity["online_update_order"] == "pass"
    assert report.integrity["future_adaptive_parameter"] == "pass"
    assert report.integrity["holdout_contamination"] == "pass"
    assert preq.n_scored > 0
    assert run.adaptive_model_id == "static_mom20"
    assert (tmp_path / "artifacts" / run.id / "prequential.json").is_file()


@pytest.mark.adaptive
def test_leaky_full_sample_fails_integrity() -> None:
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
    report, run, _preq = run_adaptive_experiment(
        bars=bars,
        instruments=instruments,
        model=get_adaptive_model("ensemble_ic_mom"),
        data_kind="synthetic",
        leaked=True,
        append=False,
    )
    assert report.integrity["future_adaptive_parameter"] == "fail"
    assert report.integrity["future_ensemble_performance"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT
    assert run.status.value == "failed"


@pytest.mark.adaptive
def test_update_before_predict_fails_integrity() -> None:
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
    report, _run, _preq = run_adaptive_experiment(
        bars=bars,
        instruments=instruments,
        model=get_adaptive_model("expanding_ic_mom20"),
        data_kind="synthetic",
        update_before_predict=True,
        append=False,
    )
    assert report.integrity["online_update_order"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT


@pytest.mark.adaptive
def test_holdout_contamination_fails() -> None:
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
    report, _run, _preq = run_adaptive_experiment(
        bars=bars,
        instruments=instruments,
        model=get_adaptive_model("ewma_ic_mom20"),
        data_kind="synthetic",
        holdout_contaminated=True,
        append=False,
    )
    assert report.integrity["holdout_contamination"] == "fail"
    assert report.integrity["future_adaptive_parameter"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT


@pytest.mark.adaptive
def test_static_vs_adaptive_comparison_records_family() -> None:
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
    report = run_adaptive_comparison(bars=bars, instruments=instruments, append=False)
    assert report.family_size == 5
    ids = {row["adaptive_model_id"] for row in report.rows}
    assert ids == {
        "static_mom20",
        "rolling_ic_mom20",
        "expanding_ic_mom20",
        "ewma_ic_mom20",
        "ensemble_ic_mom",
    }
    assert report.gate_outcome == "warn"
    assert "not market evidence" in report.note.lower()
