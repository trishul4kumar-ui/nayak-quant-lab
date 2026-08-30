from __future__ import annotations

from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.execution_research.diagnostics import monte_carlo_execution
from quantlab.execution_research.registry import get_execution_model
from quantlab.execution_research.simulator import simulate_execution


def test_same_inputs_reproduce_the_same_simulation() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    model = get_execution_model("exec_base")
    a = simulate_execution(model, bars)
    b = simulate_execution(model, bars)
    assert a.total_cost == b.total_cost
    assert a.mean_fill_ratio == b.mean_fill_ratio
    assert len(a.fills) == len(b.fills)
    assert [f.execution_price for f in a.fills] == [f.execution_price for f in b.fills]


def test_monte_carlo_seed_is_reproducible() -> None:
    bars = MemoryBarProvider(n_days=40).all_bars()
    model = get_execution_model("exec_base")
    a = monte_carlo_execution(model, bars, gross_return=0.1, n_paths=5, seed=7)
    b = monte_carlo_execution(model, bars, gross_return=0.1, n_paths=5, seed=7)
    assert a.mean_net == b.mean_net
    assert a.p5 == b.p5
