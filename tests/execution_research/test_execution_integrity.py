from __future__ import annotations

from datetime import timedelta

from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import Instrument, OHLCVBar
from quantlab.execution_research.definition import ExecutionLeakFlags
from quantlab.execution_research.experiment import run_execution_experiment
from quantlab.execution_research.registry import get_execution_model
from quantlab.execution_research.simulator import simulate_execution
from quantlab.research.gate import GateOutcome


def _instruments(bars: dict[InstrumentId, list[OHLCVBar]]) -> list[Instrument]:
    return [Instrument(id=inst, name=inst.symbol) for inst in bars]


def test_future_volume_leak_fails() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    report, _run, _sim = run_execution_experiment(
        bars=bars,
        instruments=_instruments(bars),
        definition=get_execution_model("exec_base"),
        leaks=ExecutionLeakFlags(future_volume=True),
        append=False,
    )
    assert report.integrity["future_volume_leak"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT


def test_wrong_side_slippage_fails() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    report, _run, sim = run_execution_experiment(
        bars=bars,
        instruments=_instruments(bars),
        definition=get_execution_model("exec_base"),
        leaks=ExecutionLeakFlags(wrong_side_slippage=True),
        append=False,
    )
    assert report.integrity["wrong_side_slippage"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT
    assert sim.negative_cost or any(f.slippage_cost < 0 for f in sim.fills)


def test_appending_future_volume_does_not_change_history() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    base = simulate_execution(get_execution_model("exec_base"), bars)
    mutated = {inst: list(series) for inst, series in bars.items()}
    inst = next(iter(mutated))
    last = mutated[inst][-1]
    future = last.pit.event_time + timedelta(days=10)
    mutated[inst].append(
        last.model_copy(
            update={
                "volume": 10**12,
                "pit": PointInTime(
                    event_time=future,
                    effective_time=future,
                    available_time=future,
                    ingestion_time=future,
                ),
            }
        )
    )
    replay = simulate_execution(get_execution_model("exec_base"), mutated)
    assert replay.total_cost == base.total_cost
    assert replay.mean_fill_ratio == base.mean_fill_ratio
