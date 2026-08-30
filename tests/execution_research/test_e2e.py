from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.core.config import LiveSafetyGates
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import Instrument
from quantlab.execution_research.experiment import (
    run_execution_experiment,
    run_named_execution_experiment,
)
from quantlab.execution_research.registry import get_execution_model
from quantlab.execution_research.simulator import simulate_execution
from quantlab.research.gate import GateOutcome


@pytest.mark.execution_research
def test_synthetic_cannot_promote(tmp_path: Path) -> None:
    report, run, sim = run_named_execution_experiment(
        "exec_base",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        append=True,
    )
    assert report.gate.outcome is GateOutcome.WARN
    assert report.gate.outcome is not GateOutcome.RESEARCH_CANDIDATE
    assert report.data_kind == "synthetic"
    assert sim.total_cost > 0
    assert report.net_return is not None
    assert report.gross_return is not None
    assert report.net_return < report.gross_return
    assert run.selection_stage == "execution_research"
    assert run.execution_model_id == "exec_base"
    assert LiveSafetyGates().live_trading is False
    assert (tmp_path / "artifacts" / run.id / "simulation.json").is_file()


@pytest.mark.execution_research
def test_zero_cost_is_flagged() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
    report, run, sim = run_execution_experiment(
        bars=bars,
        instruments=instruments,
        definition=get_execution_model("exec_zero_cost"),
        scenario_id="ZERO_COST",
        append=False,
    )
    assert report.integrity["zero_cost_execution"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT
    assert run.status.value == "failed"
    assert sim.total_cost == 0.0


@pytest.mark.execution_research
def test_stress_does_not_improve_cost() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    base = simulate_execution(get_execution_model("exec_base"), bars)
    stressed = simulate_execution(get_execution_model("exec_stressed"), bars)
    conservative = simulate_execution(get_execution_model("exec_conservative"), bars)
    assert stressed.total_cost >= base.total_cost
    assert conservative.total_cost >= base.total_cost
