"""PIT factor computation, look-ahead invariance, and numerical refusals."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta

import pytest

from quantlab.core.errors import AlignmentError, FactorError
from quantlab.core.identifiers import InstrumentId
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.research import CheckResult
from quantlab.factors.engine import _finite, compute_factor_panel
from quantlab.factors.market import equal_weight_market_returns, rolling_betas
from quantlab.factors.neutralize import residualize_panel
from quantlab.factors.registry import get_factor
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


@pytest.mark.factor
def test_future_bars_do_not_change_factor_at_t() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    calendar = session_calendar(bars)
    as_of = calendar[-8]
    dates = [d for d in calendar if d <= as_of]
    definition = get_factor("style_momentum_20")
    before, _ = compute_factor_panel(definition, bars, dates)
    after, _ = compute_factor_panel(definition, _append_future(bars, calendar), dates)
    assert before[as_of] == after[as_of]


@pytest.mark.factor
def test_future_bars_do_not_change_beta_at_t() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    calendar = session_calendar(bars)
    as_of = calendar[-8]
    before = rolling_betas(bars, as_of, lookback=20)
    after = rolling_betas(_append_future(bars, calendar), as_of, lookback=20)
    assert before.betas.keys() == after.betas.keys()
    for name in before.betas:
        assert before.betas[name] == pytest.approx(after.betas[name], abs=1e-12)
    assert "not nifty" in before.note.lower()


@pytest.mark.factor
def test_future_only_name_is_not_in_universe_at_t() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    calendar = session_calendar(bars)
    as_of = calendar[-8]
    before = rolling_betas(bars, as_of, lookback=20)
    extra_inst = InstrumentId.parse("NSE:FUTUREONLY")
    template = next(iter(bars.values()))[-1].model_copy(deep=True)
    template.instrument = extra_inst
    template.pit.event_time = calendar[-1] + timedelta(days=6)
    template.pit.effective_time = template.pit.event_time
    template.pit.available_time = template.pit.event_time
    template.pit.ingestion_time = template.pit.event_time
    future = deepcopy(bars)
    future[extra_inst] = [template]
    after = rolling_betas(future, as_of, lookback=20)
    assert str(extra_inst) not in after.betas
    assert set(before.betas) == set(after.betas)


@pytest.mark.factor
def test_equal_weight_market_is_cs_mean_not_nifty() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    market = equal_weight_market_returns(bars)
    assert market
    assert len(market) > 10
    assert all(value == value for value in market.values())


@pytest.mark.factor
def test_not_implemented_factor_is_empty_not_tested() -> None:
    bars = MemoryBarProvider(n_days=40).all_bars()
    panel, obs = compute_factor_panel(get_factor("size_log_cap"), bars)
    assert panel == {}
    assert obs.status is CheckResult.NOT_TESTED


@pytest.mark.factor
def test_nan_and_inf_fail_closed() -> None:
    as_of = datetime(2024, 1, 2, tzinfo=UTC)
    with pytest.raises(AlignmentError):
        _finite({"NSE:AAA": float("nan")}, as_of)
    with pytest.raises(AlignmentError):
        _finite({"NSE:AAA": float("inf")}, as_of)


@pytest.mark.factor
def test_residual_source_is_not_computed_by_engine() -> None:
    from quantlab.factors.definition import FactorSource

    bars = MemoryBarProvider(n_days=40).all_bars()
    residual = get_factor("style_momentum_20").model_copy(update={"source": FactorSource.RESIDUAL})
    with pytest.raises(FactorError, match="residualize_panel"):
        compute_factor_panel(residual, bars)


@pytest.mark.factor
def test_residualize_panel_is_not_the_original() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    dates = session_calendar(bars)
    momentum, _ = compute_factor_panel(get_factor("style_momentum_20"), bars, dates)
    beta, _ = compute_factor_panel(get_factor("market_ew_beta"), bars, dates)
    resid = residualize_panel(momentum, beta)
    last = max(set(resid) & set(momentum))
    assert resid[last] != momentum[last]
