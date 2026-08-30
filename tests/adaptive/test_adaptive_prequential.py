"""Prequential PIT: future bars cannot change state at T; predict before update."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta

import pytest

from quantlab.adaptive.engine import run_adaptive
from quantlab.adaptive.registry import get_adaptive_model
from quantlab.core.errors import AdaptiveError
from quantlab.core.identifiers import InstrumentId
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.features.engine import session_calendar


def _append_future(bars: dict[InstrumentId, list], calendar: list[datetime]) -> dict:
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


@pytest.mark.adaptive
def test_future_bars_do_not_change_state_at_t() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    calendar = session_calendar(bars)
    as_of = calendar[-8]
    prefix = {
        inst: [b for b in series if b.pit.event_time <= as_of] for inst, series in bars.items()
    }
    model = get_adaptive_model("rolling_ic_mom20")
    _p, _l, before = run_adaptive(model, prefix)
    _p2, _l2, after = run_adaptive(model, _append_future(bars, calendar))
    before_pt = next(p for p in before.points if p.as_of == as_of)
    after_pt = next(p for p in after.points if p.as_of == as_of)
    assert before_pt.n_updates_before_predict == after_pt.n_updates_before_predict
    assert before_pt.coverage == after_pt.coverage


@pytest.mark.adaptive
def test_prediction_does_not_use_todays_label() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    _p, _l, honest = run_adaptive(get_adaptive_model("expanding_ic_mom20"), bars)
    _p2, _l2, leaky = run_adaptive(
        get_adaptive_model("expanding_ic_mom20"),
        bars,
        update_before_predict=True,
    )
    mid = len(honest.points) // 2
    assert honest.points[mid].n_updates_before_predict < leaky.points[mid].n_updates_before_predict


@pytest.mark.adaptive
def test_smoothed_regime_blocked_for_prediction() -> None:
    bars = MemoryBarProvider(n_days=40).all_bars()
    model = get_adaptive_model("regime_vol_mom20").model_copy(
        update={"regime_model_id": "hmm_vol_smooth", "version": "2"}
    )
    with pytest.raises(AdaptiveError, match="smoothed"):
        run_adaptive(model, bars, predictive=True)


@pytest.mark.adaptive
def test_stale_gate_learns_from_underlying_alpha() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    for model_id in ("expanding_ic_mom20", "rolling_ic_mom20", "ewma_ic_mom20"):
        _panels, _labels, result = run_adaptive(get_adaptive_model(model_id), bars)
        assert result.final_state is not None
        assert result.final_state.n_updates >= 8
        assert result.n_predictions > 0
        assert result.n_scored > 0


@pytest.mark.adaptive
def test_static_always_emits_scores() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    model = get_adaptive_model("static_mom20")
    panels, _labels, result = run_adaptive(model, bars)
    alpha_id = model.alpha_ids[0]
    for point in result.points:
        panel = panels[alpha_id].get(point.as_of, {})
        if panel:
            assert point.coverage
    assert result.n_scored >= 8
