"""Execution-research experiments. Simulated fills cannot promote themselves."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from quantlab import __version__
from quantlab.backtest.engine import BacktestConfig, run_backtest
from quantlab.backtest.spec import config_hash
from quantlab.core.config import LiveSafetyGates
from quantlab.core.identifiers import ExperimentId, InstrumentId
from quantlab.domain.models import ExperimentRun, ExperimentStatus, Instrument, OHLCVBar
from quantlab.domain.research import CheckResult, DataLineage
from quantlab.execution_research.attribution import (
    AlphaExecutionAttribution,
    CostAttribution,
    alpha_execution_attribution,
    cost_attribution,
)
from quantlab.execution_research.capacity import CapacityReport, capacity_analysis
from quantlab.execution_research.definition import (
    ExecutionLeakFlags,
    MarketMicrostructureDefinition,
)
from quantlab.execution_research.diagnostics import (
    MonteCarloReport,
    fragility_score,
    monte_carlo_execution,
)
from quantlab.execution_research.registry import get_execution_model
from quantlab.execution_research.scenarios import scenario_model
from quantlab.execution_research.sensitivity import SensitivityReport, sensitivity_report
from quantlab.execution_research.simulator import SimulationResult, simulate_execution
from quantlab.execution_research.validation import (
    full_fill_assumption,
    hidden_partial,
    wrong_side_from_fills,
    zero_cost_execution,
)
from quantlab.models.registry import ExperimentLedger
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.research.gate import GateOutcome, ResearchGateResult, evaluate_research_gate
from quantlab.research.integrity import evaluate_integrity
from quantlab.research.momentum import CrossSectionalMomentum
from quantlab.risk.firewall import RiskFirewall, RiskLimits


class ExecutionExperimentReport(BaseModel):
    schema_version: str = "1"
    execution_model_id: str
    identity_hash: str
    scenario_id: str
    scenario_version: str = "1"
    simulation: SimulationResult
    attribution: CostAttribution
    alpha_attribution: AlphaExecutionAttribution
    sensitivity: SensitivityReport
    capacity: CapacityReport
    monte_carlo: MonteCarloReport
    fragility_score: float
    fragility_flags: list[str] = Field(default_factory=list)
    gate: ResearchGateResult
    integrity: dict[str, str] = Field(default_factory=dict)
    data_kind: str = "synthetic"
    gross_return: float | None = None
    net_return: float | None = None
    note: str = (
        "Simulated execution is not a broker fill. Synthetic volume is not NSE ADV. "
        "Uncalibrated impact is not market evidence. Prompt 05 remains the promotion gate."
    )


def run_execution_experiment(
    *,
    bars: dict[InstrumentId, list[OHLCVBar]],
    instruments: list[Instrument],
    definition: MarketMicrostructureDefinition,
    data_kind: str = "synthetic",
    dataset_id: str = "",
    dataset_version: str = "",
    snapshot_id: str = "",
    checksum: str = "",
    family_size: int = 1,
    ledger_path: Path | None = None,
    append: bool = False,
    leaks: ExecutionLeakFlags | None = None,
    capital: float = 1_000_000.0,
    scenario_id: str = "BASE",
    lookback: int = 20,
) -> tuple[ExecutionExperimentReport, ExperimentRun, SimulationResult]:
    flags = leaks or ExecutionLeakFlags()
    sim = simulate_execution(definition, bars, capital=capital, lookback=lookback, leaks=flags)
    firewall = RiskFirewall(RiskLimits(max_name_weight=0.55, max_names=5, max_gross=1.05))
    firewall.register_instruments(instruments)
    gross = run_backtest(
        bars,
        CrossSectionalMomentum(lookback=lookback, top_n=2),
        firewall,
        BacktestConfig(lookback=lookback, cost_bps=0.0, slippage_bps=0.0, initial_equity=capital),
    )
    attr = cost_attribution(sim)
    alpha_attr = alpha_execution_attribution(
        gross_return=gross.total_return, total_cost=sim.total_cost, capital=capital
    )
    sens = sensitivity_report(definition, bars, capital=capital)
    cap = capacity_analysis(definition, bars, lookback=lookback)
    mc = monte_carlo_execution(
        definition,
        bars,
        gross_return=gross.total_return,
        capital=capital,
        seed=definition.seed,
    )
    stressed = simulate_execution(
        get_execution_model("exec_stressed"), bars, capital=capital, lookback=lookback
    )
    frag = fragility_score(
        base_cost=sim.total_cost,
        stress_cost=stressed.total_cost,
        fill_ratio=sim.mean_fill_ratio,
        latency_sessions=definition.latency_sessions,
    )
    wrong_slip, wrong_impact = wrong_side_from_fills(sim)
    zero = zero_cost_execution(definition, sim)
    cost_for_gate = definition.cost.total_bps()
    integrity = evaluate_integrity(
        bars=[bar for series in bars.values() for bar in series],
        states=[],
        as_of_times=[f.timestamp for f in sim.fills],
        next_bar_fill=True,
        cost_bps=cost_for_gate if cost_for_gate > 0 else 0.0,
        slippage_model=definition.slippage_model.value,
        live_trading=LiveSafetyGates().live_trading,
        n_experiments_in_family=family_size,
        used_ml=False,
        data_kind=data_kind,
        pit_query_verified=True,
        future_volume_leak=flags.future_volume,
        future_spread_leak=flags.future_spread,
        future_liquidity_leak=flags.future_liquidity,
        future_impact_parameter=flags.future_impact_parameter,
        future_execution_parameter=flags.future_execution_parameter,
        future_latency=flags.future_latency,
        pre_arrival_fill=flags.pre_arrival_fill,
        full_fill_assumption=full_fill_assumption(definition, flags),
        zero_cost_execution=zero,
        negative_execution_cost=sim.negative_cost,
        wrong_side_slippage=flags.wrong_side_slippage or wrong_slip,
        wrong_side_impact=flags.wrong_side_impact or wrong_impact,
        hidden_partial_fill=flags.hidden_partial_fill or hidden_partial(sim),
        capacity_lookahead=flags.capacity_lookahead,
        execution_model_mutation=flags.model_mutation,
        future_execution_calibration=flags.future_calibration,
    )
    gate = evaluate_research_gate(
        integrity_failed=integrity.failed(),
        next_bar_fill=True,
        cost_bps=cost_for_gate,
        data_kind=data_kind,
        walk_forward_windows=max(sim.n_fills, 1),
        oos_sharpe=None,
        cost_still_positive_at_20bps=None,
        parameter_fragile=False,
        statistical_status=CheckResult.WARN,
        n_hypotheses=family_size,
        test_used_for_selection=False,
    )
    report = ExecutionExperimentReport(
        execution_model_id=definition.definition_id,
        identity_hash=definition.identity_hash(),
        scenario_id=scenario_id,
        simulation=sim,
        attribution=attr,
        alpha_attribution=alpha_attr,
        sensitivity=sens,
        capacity=cap,
        monte_carlo=mc,
        fragility_score=frag.score,
        fragility_flags=frag.flags,
        gate=gate,
        integrity=integrity.as_str_map(),
        data_kind=data_kind,
        gross_return=gross.total_return,
        net_return=alpha_attr.net_edge,
    )
    run = _ledger_row(
        definition,
        report,
        instruments,
        dataset_id,
        dataset_version,
        snapshot_id,
        checksum,
        family_size,
        capital,
        scenario_id,
    )
    if append and ledger_path is not None:
        ExperimentLedger(ledger_path).append(run)
        _write_artifacts(ledger_path.parent / "artifacts", run, report, definition)
    return report, run, sim


def run_named_execution_experiment(
    model_id: str,
    *,
    ledger_path: Path,
    n_days: int = 80,
    family_size: int = 1,
    fabric_root: Path | None = None,
    append: bool = True,
    leaks: ExecutionLeakFlags | None = None,
    capital: float = 1_000_000.0,
    scenario_id: str | None = None,
) -> tuple[ExecutionExperimentReport, ExperimentRun, SimulationResult]:
    from quantlab.research.pipeline import load_synthetic_frame

    frame = load_synthetic_frame(n_days=n_days, ledger_path=ledger_path, fabric_root=fabric_root)
    if scenario_id:
        definition = scenario_model(scenario_id)
        sid = scenario_id
    else:
        definition = get_execution_model(model_id)
        sid = model_id
    return run_execution_experiment(
        bars=frame.bars,
        instruments=frame.instruments,
        definition=definition,
        data_kind=frame.record.data_kind.value,
        dataset_id=frame.record.dataset_id,
        dataset_version=frame.record.version,
        snapshot_id=frame.record.snapshot_id,
        checksum=frame.record.checksum,
        family_size=family_size,
        ledger_path=ledger_path,
        append=append,
        leaks=leaks,
        capital=capital,
        scenario_id=sid,
    )


def _ledger_row(
    definition: MarketMicrostructureDefinition,
    report: ExecutionExperimentReport,
    instruments: list[Instrument],
    dataset_id: str,
    dataset_version: str,
    snapshot_id: str,
    checksum: str,
    family_size: int,
    capital: float,
    scenario_id: str,
) -> ExperimentRun:
    env = environment()
    status = (
        ExperimentStatus.FAILED
        if report.gate.outcome is GateOutcome.REJECT
        else ExperimentStatus.PASSED
    )
    lineage = DataLineage(
        provider="execution_research",
        dataset_version=dataset_version,
        ingested_at=datetime.now(tz=UTC),
        transformations=["pit_execution_simulation"],
        dataset_id=dataset_id,
        snapshot_id=snapshot_id,
        data_kind=report.data_kind,
        checksum=checksum,
        source="prompt13",
    )
    metrics: dict[str, float] = {
        "total_cost": report.simulation.total_cost,
        "mean_fill_ratio": report.simulation.mean_fill_ratio,
        "n_fills": float(report.simulation.n_fills),
        "fragility": report.fragility_score,
        "capital": capital,
        "cost_bps": definition.cost.total_bps(),
    }
    if report.gross_return is not None:
        metrics["gross_return"] = report.gross_return
    if report.net_return is not None:
        metrics["net_return"] = report.net_return
    return ExperimentRun(
        id=str(ExperimentId()),
        name=f"execution_{definition.definition_id}",
        hypothesis="an apparent edge must survive execution friction before it is tradable",
        status=status,
        git_commit=git_commit(),
        dataset_version=dataset_version or "unspecified",
        universe=[str(i.id) for i in instruments],
        transaction_cost_bps=definition.cost.total_bps(),
        slippage_model=definition.slippage_model.value,
        latency_model=definition.latency_model.value,
        dataset_id=dataset_id,
        snapshot_id=snapshot_id,
        data_kind=report.data_kind,
        lineage=lineage.as_dict(),
        metrics=metrics,
        integrity=report.integrity,
        application_version=__version__,
        conclusion=report.note,
        config_hash=config_hash(
            {
                "execution": definition.identity_hash(),
                "scenario": scenario_id,
                "capital": capital,
                "seed": definition.seed,
            }
        ),
        research_family_id="execution_research",
        n_hypotheses_in_family=family_size,
        selection_stage="execution_research",
        gate_outcome=report.gate.outcome.value,
        gate_reasons=report.gate.as_str_map(),
        git_dirty=git_dirty(),
        python_version=env.get("python", ""),
        validation={"path": "execution_research", "prompt05_suite": "not_run"},
        random_seed=definition.seed,
        feature_identity_hash=definition.identity_hash(),
        execution_model_id=definition.definition_id,
        execution_model_version=definition.version,
        scenario_id=scenario_id,
        scenario_version="1",
        strategy_id="cs_momentum_v1",
        cost_model=definition.cost.provenance,
    )


def _write_artifacts(
    root: Path,
    run: ExperimentRun,
    report: ExecutionExperimentReport,
    definition: MarketMicrostructureDefinition,
) -> None:
    import json

    folder = root / run.id
    folder.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "config": {
            "experiment_id": run.id,
            "config_hash": run.config_hash,
            "execution_model_id": definition.definition_id,
            "identity_hash": definition.identity_hash(),
            "scenario_id": report.scenario_id,
            "data_kind": report.data_kind,
            "seed": run.random_seed,
        },
        "microstructure_definition": definition.model_dump(mode="json"),
        "simulation": report.simulation.model_dump(mode="json"),
        "attribution": report.attribution.model_dump(mode="json"),
        "capacity": report.capacity.model_dump(mode="json"),
        "sensitivity": report.sensitivity.model_dump(mode="json"),
        "integrity": run.integrity,
        "lineage": run.lineage,
        "validation": run.validation,
    }
    for name, body in payload.items():
        (folder / f"{name}.json").write_text(
            json.dumps(body, indent=2, default=str), encoding="utf-8"
        )
