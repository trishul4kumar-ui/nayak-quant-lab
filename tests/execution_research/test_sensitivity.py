from __future__ import annotations

from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.execution_research.registry import get_execution_model
from quantlab.execution_research.sensitivity import sensitivity_report


def test_wider_spread_does_not_reduce_cost() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    report = sensitivity_report(get_execution_model("exec_base"), bars)
    costs = [row.total_cost for row in report.spread]
    assert costs == sorted(costs)
