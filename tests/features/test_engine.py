from datetime import UTC, datetime, timedelta

import pytest

from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import BarInterval, OHLCVBar
from quantlab.features.engine import compute_panel, compute_value, pit_bars, session_calendar
from quantlab.features.registry import FeatureRegistry, get_feature
from quantlab.market.state import build_market_state


def test_momentum_matches_market_state_formula() -> None:
    provider = MemoryBarProvider(n_days=80)
    inst = provider.get_instruments()[0]
    series = provider.all_bars()[inst.id]
    as_of = series[25].pit.event_time
    state = build_market_state(series, as_of, lookback=20)
    obs = compute_value(get_feature("momentum_20"), series, as_of)
    assert state is not None
    assert obs.value is not None
    assert obs.value == pytest.approx(state.features["momentum_20"])
    prices = [b.close for b in pit_bars(series, as_of)]
    expected = prices[-1] / prices[-1 - 20] - 1.0
    assert obs.value == pytest.approx(expected)


@pytest.mark.parametrize("lookback", [1, 5, 10, 20])
def test_trailing_return_matches_definition(lookback: int) -> None:
    provider = MemoryBarProvider(n_days=80)
    inst = provider.get_instruments()[0]
    series = provider.all_bars()[inst.id]
    as_of = series[-1].pit.event_time
    obs = compute_value(get_feature(f"momentum_{lookback}"), series, as_of)
    prices = [b.close for b in pit_bars(series, as_of)]
    assert obs.value == pytest.approx(prices[-1] / prices[-1 - lookback] - 1.0)


def test_future_bars_cannot_change_historical_feature() -> None:
    provider = MemoryBarProvider(n_days=80)
    inst = provider.get_instruments()[0]
    series = list(provider.all_bars()[inst.id])
    as_of = series[20].pit.event_time
    before = compute_value(get_feature("momentum_5"), series, as_of)
    future = series[-1].model_copy(deep=True)
    future.close = 9_999.0
    future.pit = PointInTime(
        event_time=as_of + timedelta(days=10),
        effective_time=as_of + timedelta(days=10),
        available_time=as_of + timedelta(days=10),
        ingestion_time=as_of + timedelta(days=10),
    )
    after = compute_value(get_feature("momentum_5"), series + [future], as_of)
    assert before.value == after.value


def test_late_available_print_is_excluded() -> None:
    day = datetime(2024, 1, 2, tzinfo=UTC)
    later = datetime(2024, 1, 5, tzinfo=UTC)
    inst = InstrumentId.parse("NSE:TCS")
    bar = OHLCVBar(
        instrument=inst,
        pit=PointInTime(
            event_time=day, effective_time=day, available_time=later, ingestion_time=later
        ),
        interval=BarInterval.DAY,
        open=10,
        high=11,
        low=9,
        close=10,
        volume=1_000,
    )
    assert pit_bars([bar], day) == []


def test_identity_changes_when_formula_changes() -> None:
    base = get_feature("momentum_20")
    changed = base.model_copy(
        update={"version": "2", "mathematical_definition": "log(close[t]/close[t-20])"}
    )
    assert changed.identity_hash() != base.identity_hash()


def test_registry_refuses_overwrite() -> None:
    registry = FeatureRegistry()
    with pytest.raises(ValueError, match="cannot overwrite"):
        registry.register(get_feature("momentum_20"))


def test_same_snapshot_same_panel() -> None:
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    dates = session_calendar(bars)
    feature = get_feature("momentum_10")
    a = compute_panel(feature, bars, dates)
    b = compute_panel(feature, bars, dates)
    assert a == b


def test_rolling_beta_is_not_implemented() -> None:
    provider = MemoryBarProvider(n_days=80)
    inst = provider.get_instruments()[0]
    series = provider.all_bars()[inst.id]
    obs = compute_value(get_feature("rolling_beta_20"), series, series[-1].pit.event_time)
    assert obs.value is None
    assert "NOT_TESTED" in obs.note
