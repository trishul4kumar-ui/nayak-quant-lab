"""Regime experiments use the Prompt 05 gate. Synthetic cannot promote."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import Instrument
from quantlab.domain.research import CheckResult
from quantlab.features.engine import Panel
from quantlab.regimes.condition import conditional_ic
from quantlab.regimes.detectors import RegimeObservation
from quantlab.regimes.duration import durations
from quantlab.regimes.engine import classify, compute_state_panel
from quantlab.regimes.experiment import run_named_regime_experiment, run_regime_experiment
from quantlab.regimes.registry import get_regime_model
from quantlab.regimes.transitions import transition_matrix
from quantlab.research.gate import GateOutcome


@pytest.mark.regime
def test_synthetic_regime_cannot_promote(tmp_path: Path) -> None:
    report, run, snaps, observations = run_named_regime_experiment(
        "vol_tercile",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        append=True,
    )
    assert report.gate.outcome is GateOutcome.WARN
    assert report.gate.outcome is not GateOutcome.RESEARCH_CANDIDATE
    assert report.data_kind == "synthetic"
    assert report.integrity["synthetic_data"] == "warn"
    assert report.integrity["future_regime"] == "pass"
    assert report.integrity["hmm_smoothing"] == "pass"
    assert snaps
    assert observations
    assert run.regime_model_id == "vol_tercile"
    assert (tmp_path / "ledger.jsonl").exists()
    assert (tmp_path / "artifacts" / run.id / "transitions.json").is_file()


@pytest.mark.regime
def test_leaky_regime_fails_integrity() -> None:
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
    report, run, _snaps, _obs = run_regime_experiment(
        bars=bars,
        instruments=instruments,
        model=get_regime_model("vol_tercile"),
        data_kind="synthetic",
        leaked=True,
        hmm_smoothing=True,
        full_sample_fit=True,
        append=False,
    )
    assert report.integrity["future_regime"] == "fail"
    assert report.integrity["hmm_smoothing"] == "fail"
    assert report.integrity["full_sample_regime_fit"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT
    assert run.status.value == "failed"


@pytest.mark.regime
def test_transition_rows_sum_to_one() -> None:
    observations = classify(
        get_regime_model("vol_tercile"),
        compute_state_panel(MemoryBarProvider(n_days=80).all_bars()),
    )
    matrix = transition_matrix(observations)
    assert matrix.n_transitions > 0
    for row in matrix.probabilities:
        assert sum(row) == pytest.approx(1.0)


@pytest.mark.regime
def test_durations_match_run_lengths() -> None:
    start = datetime(2024, 1, 2, tzinfo=UTC)
    labels = ["low", "low", "high", "high", "high"]
    observations = [
        RegimeObservation(
            as_of=start + timedelta(days=i),
            hard_label=label,
            method="rule",
        )
        for i, label in enumerate(labels)
    ]
    report = durations(observations)
    assert report.n_runs["low"] == 1
    assert report.n_runs["high"] == 1
    assert report.mean["low"] == pytest.approx(2.0)
    assert report.mean["high"] == pytest.approx(3.0)


@pytest.mark.regime
def test_insufficient_regime_sample_is_not_tested() -> None:
    start = datetime(2024, 1, 2, tzinfo=UTC)
    observations = [
        RegimeObservation(as_of=start + timedelta(days=i), hard_label="low", method="rule")
        for i in range(3)
    ]
    empty: Panel = {}
    slice_ = conditional_ic(empty, empty, observations, "low", min_sample=8)
    assert slice_.status is CheckResult.NOT_TESTED
    assert slice_.n < 8
