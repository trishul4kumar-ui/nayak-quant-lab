from __future__ import annotations

from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.execution_research.registry import get_execution_model
from quantlab.execution_research.scenarios import scenario_model
from quantlab.execution_research.simulator import simulate_execution


def test_stressed_scenario_costs_at_least_as_much_as_base() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    base = simulate_execution(scenario_model("BASE"), bars)
    stressed = simulate_execution(get_execution_model("exec_stressed"), bars)
    assert stressed.total_cost >= base.total_cost
