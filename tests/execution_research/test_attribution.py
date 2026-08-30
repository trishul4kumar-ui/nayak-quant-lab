from __future__ import annotations

from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import Instrument
from quantlab.execution_research.experiment import run_execution_experiment
from quantlab.execution_research.registry import get_execution_model
from quantlab.research.gate import GateOutcome


def test_gross_minus_drag_is_net() -> None:
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
    report, _run, sim = run_execution_experiment(
        bars=bars,
        instruments=instruments,
        definition=get_execution_model("exec_base"),
        append=False,
    )
    assert report.gross_return is not None
    assert report.net_return is not None
    drag = sim.total_cost / sim.capital
    assert abs(report.net_return - (report.gross_return - drag)) < 1e-12
    assert report.gate.outcome is not GateOutcome.RESEARCH_CANDIDATE
    assert sim.total_cost > 0
