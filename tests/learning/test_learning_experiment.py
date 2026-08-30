"""Model experiments use the Prompt 05 gate. Leaks FAIL. Synthetic cannot promote."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import Instrument
from quantlab.learning.experiment import (
    run_model_comparison,
    run_model_experiment,
    run_named_model_experiment,
)
from quantlab.learning.registry import get_model
from quantlab.learning.walkforward import LeakFlags
from quantlab.research.gate import GateOutcome


def _frame() -> tuple[dict, list[Instrument]]:
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
    return bars, instruments


@pytest.mark.learning
def test_synthetic_model_cannot_promote(tmp_path: Path) -> None:
    report, run, wf = run_named_model_experiment(
        "ols_mom",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        append=True,
    )
    assert report.gate.outcome is GateOutcome.WARN
    assert report.gate.outcome is not GateOutcome.RESEARCH_CANDIDATE
    assert report.data_kind == "synthetic"
    assert report.integrity["model_replay_leak"] == "pass"
    assert report.integrity["future_pca"] == "pass"
    assert wf.n_scored > 0
    assert run.statistical_model_id == "ols_mom"
    assert (tmp_path / "artifacts" / run.id / "walkforward.json").is_file()


@pytest.mark.learning
def test_full_sample_replay_fails() -> None:
    bars, instruments = _frame()
    report, run, _wf = run_model_experiment(
        bars=bars,
        instruments=instruments,
        model=get_model("ols_mom"),
        data_kind="synthetic",
        leaks=LeakFlags(replay_full_sample=True),
        append=False,
    )
    assert report.integrity["model_replay_leak"] == "fail"
    assert report.integrity["future_model_training"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT
    assert run.status.value == "failed"


@pytest.mark.learning
def test_future_pca_fails() -> None:
    bars, instruments = _frame()
    report, _run, _wf = run_model_experiment(
        bars=bars,
        instruments=instruments,
        model=get_model("pca_ols_mom"),
        data_kind="synthetic",
        leaks=LeakFlags(future_pca=True),
        append=False,
    )
    assert report.integrity["future_pca"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT


@pytest.mark.learning
def test_future_selection_fails() -> None:
    bars, instruments = _frame()
    report, _run, _wf = run_model_experiment(
        bars=bars,
        instruments=instruments,
        model=get_model("select_ols_mom"),
        data_kind="synthetic",
        leaks=LeakFlags(future_selection=True),
        append=False,
    )
    assert report.integrity["future_feature_selection"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT


@pytest.mark.learning
def test_label_as_feature_fails() -> None:
    bars, instruments = _frame()
    report, _run, _wf = run_model_experiment(
        bars=bars,
        instruments=instruments,
        model=get_model("ols_mom"),
        data_kind="synthetic",
        leaks=LeakFlags(label_as_feature=True),
        append=False,
    )
    assert report.integrity["label_as_feature"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT


@pytest.mark.learning
def test_holdout_and_hyperparameter_fail() -> None:
    bars, instruments = _frame()
    report, _run, _wf = run_model_experiment(
        bars=bars,
        instruments=instruments,
        model=get_model("ridge_mom"),
        data_kind="synthetic",
        leaks=LeakFlags(holdout_contaminated=True, future_hyperparameter=True),
        append=False,
    )
    assert report.integrity["holdout_contamination"] == "fail"
    assert report.integrity["future_hyperparameter"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT


@pytest.mark.learning
def test_linear_vs_regularized_family() -> None:
    bars, instruments = _frame()
    report = run_model_comparison(
        bars=bars,
        instruments=instruments,
        model_ids=["alpha_mom20", "ols_mom", "ridge_mom", "lasso_mom", "elastic_mom"],
        append=False,
    )
    assert report.family_size == 5
    assert report.gate_outcome == "warn"
    assert "not market evidence" in report.note.lower()
