"""Walk-forward PIT: future bars cannot change the fit at T; leaks FAIL."""

from __future__ import annotations

from copy import deepcopy
from datetime import timedelta

import pytest

from quantlab.core.errors import ModelError
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.features.engine import session_calendar
from quantlab.learning.engine import run_learning
from quantlab.learning.registry import get_model


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


@pytest.mark.learning
def test_future_bars_do_not_change_n_train_at_t() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    calendar = session_calendar(bars)
    as_of = calendar[-8]
    prefix = {
        inst: [b for b in series if b.pit.event_time <= as_of] for inst, series in bars.items()
    }
    model = get_model("ols_mom")
    _d, _p, before, _r = run_learning(model, prefix)
    _d2, _p2, after, _r2 = run_learning(model, _append_future(bars, calendar))
    before_pt = next(p for p in before.points if p.as_of == as_of)
    after_pt = next(p for p in after.points if p.as_of == as_of)
    assert before_pt.n_train == after_pt.n_train
    assert before_pt.coverage == after_pt.coverage


@pytest.mark.learning
def test_smoothed_regime_blocked() -> None:
    bars = MemoryBarProvider(n_days=40).all_bars()
    model = get_model("regime_ols_mom").model_copy(
        update={"regime_model_id": "hmm_vol_smooth", "version": "2"}
    )
    with pytest.raises(ModelError, match="smoothed"):
        run_learning(model, bars, predictive=True)


@pytest.mark.learning
def test_alpha_passthrough_scores() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    _dataset, predictions, result, _reg = run_learning(get_model("alpha_mom20"), bars)
    assert result.n_scored >= 8
    assert any(predictions.values())
