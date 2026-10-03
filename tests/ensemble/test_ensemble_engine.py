"""PIT combine: future bars cannot change scores at T; leaks FAIL."""

from __future__ import annotations

from copy import deepcopy
from datetime import timedelta

import pytest

from quantlab.core.errors import EnsembleError, InfeasibleEnsemble
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.ensemble.definition import EnsembleLeakFlags
from quantlab.ensemble.engine import run_ensemble
from quantlab.ensemble.registry import get_ensemble
from quantlab.ensemble.weighting import constrain_weights
from quantlab.features.engine import session_calendar


def _append_future(bars: dict, calendar: list) -> dict:
    future = deepcopy(bars)
    for inst, series in future.items():
        extra = series[-1].model_copy(deep=True)
        extra.pit.event_time = calendar[-1] + timedelta(days=5)
        extra.pit.effective_time = extra.pit.event_time
        extra.pit.available_time = extra.pit.event_time
        extra.pit.ingestion_time = extra.pit.event_time
        extra.close = extra.close * 1.75
        future[inst] = series + [extra]
    return future


@pytest.mark.ensemble
def test_future_bars_do_not_change_historical_scores() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    calendar = session_calendar(bars)
    as_of = calendar[-8]
    prefix = {
        inst: [b for b in series if b.pit.event_time <= as_of] for inst, series in bars.items()
    }
    definition = get_ensemble("ew_mom_5_20")
    _p, _l, before = run_ensemble(definition, prefix)
    _p2, _l2, after = run_ensemble(definition, _append_future(bars, calendar))
    before_pt = next(p for p in before.points if p.as_of == as_of)
    after_pt = next(p for p in after.points if p.as_of == as_of)
    assert before.predictions[as_of] == after.predictions[as_of]
    assert before_pt.weights == after_pt.weights
    assert before_pt.coverage == after_pt.coverage


@pytest.mark.ensemble
def test_smoothed_regime_blocked() -> None:
    bars = MemoryBarProvider(n_days=40).all_bars()
    definition = get_ensemble("regime_ew_mom").model_copy(
        update={"regime_model_id": "hmm_vol_smooth", "version": "2"}
    )
    with pytest.raises(EnsembleError, match="smoothed"):
        run_ensemble(definition, bars, predictive=True)


@pytest.mark.ensemble
def test_equal_weight_is_one_over_n() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    _p, _l, result = run_ensemble(get_ensemble("ew_mom_5_20"), bars)
    last = result.weights_path[-1]
    assert abs(last["rank_momentum_5"] - 0.5) < 1e-9
    assert abs(last["rank_momentum_20"] - 0.5) < 1e-9
    assert result.n_scored > 0
    assert result.best_component_id is not None
    assert result.equal_weight_ic is not None


@pytest.mark.ensemble
def test_hard_constraints_are_not_relaxed() -> None:
    definition = get_ensemble("ew_mom_5_20").model_copy(update={"min_weight": 0.6, "version": "2"})
    with pytest.raises(InfeasibleEnsemble, match="min_weight"):
        constrain_weights(
            {"rank_momentum_5": 0.5, "rank_momentum_20": 0.5},
            definition,
        )


@pytest.mark.ensemble
def test_stacking_uses_history() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    _p, _l, result = run_ensemble(get_ensemble("ridge_stack_mom"), bars)
    assert result.n_scored >= 8
    _p2, _l2, leaked = run_ensemble(
        get_ensemble("ridge_stack_mom"),
        bars,
        leaks=EnsembleLeakFlags(stacking_leak=True),
    )
    assert leaked.note.startswith("leaky")
    assert leaked.n_scored >= 0


@pytest.mark.ensemble
@pytest.mark.parametrize("flag", list(EnsembleLeakFlags.model_fields))
def test_every_declared_leakage_flag_forces_failure(flag: str) -> None:
    bars = MemoryBarProvider(n_days=40).all_bars()
    _panels, _labels, result = run_ensemble(
        get_ensemble("ew_mom_5_20"), bars, leaks=EnsembleLeakFlags(**{flag: True})
    )
    assert result.status.value == "fail"
