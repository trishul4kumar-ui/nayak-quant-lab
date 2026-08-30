from __future__ import annotations

from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.execution_research.definition import LiquidityKind
from quantlab.execution_research.liquidity import liquidity_profile


def test_unknown_liquidity_is_not_infinite() -> None:
    provider = MemoryBarProvider(n_days=20)
    inst = next(iter(provider.all_bars()))
    series = provider.all_bars()[inst]
    profile = liquidity_profile(
        series,
        security_id=str(inst),
        as_of=series[-1].pit.available_time,
        max_participation=0.2,
        kind=LiquidityKind.UNKNOWN,
        lookback=20,
    )
    assert profile.session_volume is None
    assert profile.capacity_status == "not_tested"


def test_synthetic_volume_is_labelled() -> None:
    provider = MemoryBarProvider(n_days=20)
    inst = next(iter(provider.all_bars()))
    series = provider.all_bars()[inst]
    profile = liquidity_profile(
        series,
        security_id=str(inst),
        as_of=series[10].pit.available_time,
        max_participation=0.2,
        kind=LiquidityKind.BAR_VOLUME,
        lookback=5,
    )
    assert profile.session_volume is not None
    assert "NSE ADV" in profile.note
    assert profile.as_of == series[10].pit.available_time
