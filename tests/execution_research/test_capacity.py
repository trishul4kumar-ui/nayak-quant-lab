from __future__ import annotations

from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.execution_research.capacity import capacity_analysis
from quantlab.execution_research.registry import get_execution_model


def test_larger_notional_worsens_participation_or_fill_ratio() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    report = capacity_analysis(get_execution_model("exec_low_liquidity"), bars)
    small = report.rows[0]
    large = report.rows[-1]
    assert large.capital > small.capital
    assert large.mean_fill_ratio <= small.mean_fill_ratio + 1e-9
    assert report.status == "not_tested"
