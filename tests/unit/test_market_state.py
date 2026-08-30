from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.market.state import build_cross_section, build_market_state


def test_market_state_momentum_uses_available_bars_only() -> None:
    provider = MemoryBarProvider(n_days=40)
    inst = provider.get_instruments()[0]
    series = provider.all_bars()[inst.id]
    as_of = series[25].pit.event_time
    state = build_market_state(series, as_of, lookback=20)
    assert state is not None
    assert state.pit.is_available_at(as_of)
    assert "momentum_20" in state.features
    later = series[-1].pit.event_time
    assert as_of <= later


def test_cross_section_covers_universe() -> None:
    provider = MemoryBarProvider(n_days=40)
    as_of = list(provider.all_bars().values())[0][25].pit.event_time
    states = build_cross_section(provider.all_bars(), as_of, lookback=20)
    assert len(states) == len(provider.get_instruments())
