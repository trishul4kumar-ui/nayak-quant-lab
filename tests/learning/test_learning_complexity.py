"""Complexity can overfit. Incremental IC is a comparison, not a trophy."""

from __future__ import annotations

import pytest

from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import Instrument
from quantlab.learning.engine import run_learning
from quantlab.learning.experiment import run_model_experiment
from quantlab.learning.registry import get_model
from quantlab.learning.walkforward import LeakFlags


@pytest.mark.learning
def test_complexity_can_overfit_zero_signal() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    leaks = LeakFlags(permute_labels=True)
    _d, _p, mean_wf, _r = run_learning(get_model("mean_baseline"), bars, leaks=leaks)
    _d2, _p2, rf_wf, _r2 = run_learning(get_model("rf_mom"), bars, leaks=leaks)
    assert mean_wf.train_rmse is not None
    assert rf_wf.train_rmse is not None
    assert rf_wf.train_rmse <= mean_wf.train_rmse + 1e-9
    if rf_wf.mean_ic is not None:
        assert abs(rf_wf.mean_ic) < 0.95


@pytest.mark.learning
def test_incremental_report_is_present() -> None:
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
    report, _run, wf = run_model_experiment(
        bars=bars,
        instruments=instruments,
        model=get_model("ols_mom"),
        data_kind="synthetic",
        append=False,
    )
    assert report.incremental is not None
    assert wf.n_scored > 0
    assert report.importance.method in {"abs_coefficient", "none"}


@pytest.mark.learning
def test_linear_vs_nonlinear_runs() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    _d, _p, ridge, _r = run_learning(get_model("ridge_mom"), bars)
    _d2, _p2, forest, _r2 = run_learning(get_model("rf_mom"), bars)
    assert ridge.n_scored > 0
    assert forest.n_scored > 0
