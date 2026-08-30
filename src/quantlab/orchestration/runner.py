"""Execute frozen research plans by calling existing engines. Not a second backtester."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab import __version__
from quantlab.alpha.definition import get_alpha
from quantlab.backtest.engine import BacktestConfig, BacktestResult, run_backtest
from quantlab.backtest.spec import config_hash
from quantlab.core.config import LiveSafetyGates
from quantlab.core.identifiers import ExperimentId
from quantlab.domain.models import ExperimentRun, ExperimentStatus, Instrument
from quantlab.domain.research import CheckResult, DataLineage
from quantlab.execution_research.registry import get_execution_model
from quantlab.execution_research.simulator import simulate_execution
from quantlab.features.registry import get_feature
from quantlab.models.registry import ExperimentLedger
from quantlab.orchestration.ablation import ablating_lookback
from quantlab.orchestration.budget import ResearchBudget, apply_budget
from quantlab.orchestration.cache import OrchestrationCache
from quantlab.orchestration.comparison import compare_candidates
from quantlab.orchestration.contracts import ExperimentType, ResearchQuality, ResearchStatus
from quantlab.orchestration.discovery import summarize_discovery
from quantlab.orchestration.falsification import (
    EqualWeightBaseline,
    InvertedMomentum,
    falsification_summary,
)
from quantlab.orchestration.family import degrees_of_freedom
from quantlab.orchestration.leaks import OrchestrationLeakFlags
from quantlab.orchestration.lineage import assert_lineage_intact, build_graph
from quantlab.orchestration.multiple_testing import family_correction
from quantlab.orchestration.pareto import pareto_front
from quantlab.orchestration.registry import OrchestrationRegistry, default_registry
from quantlab.orchestration.report import OrchestrationReport
from quantlab.orchestration.robustness import robustness_summary
from quantlab.orchestration.scheduler import run_isolated
from quantlab.orchestration.search_space import ResearchCandidate, expand_grid
from quantlab.orchestration.selection import CandidateOutcome, select_primary
from quantlab.orchestration.sensitivity import cost_sensitivity
from quantlab.orchestration.snapshot import DatasetSnapshot, pin_from_frame
from quantlab.orchestration.specification import ResearchSpec
from quantlab.orchestration.stopping import StoppingRule, assert_not_posthoc
from quantlab.portfolio.spec import get_portfolio_model
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.research.gate import GateOutcome, evaluate_research_gate
from quantlab.research.integrity import evaluate_integrity
from quantlab.research.momentum import CrossSectionalMomentum
from quantlab.research.statistics import sign_flip_p_value
from quantlab.risk.firewall import RiskFirewall, RiskLimits


def _period_returns(curve: list[float]) -> list[float]:
    out: list[float] = []
    for i in range(1, len(curve)):
        prev = curve[i - 1]
        if prev > 0:
            out.append(curve[i] / prev - 1.0)
    return out


def _strategy_for(candidate: ResearchCandidate) -> Any:
    if candidate.strategy_id == "equal_weight":
        return EqualWeightBaseline()
    if candidate.strategy_id == "cs_momentum_inverted":
        return InvertedMomentum(lookback=candidate.lookback, top_n=candidate.top_n)
    return CrossSectionalMomentum(lookback=candidate.lookback, top_n=candidate.top_n)


def _run_candidate(
    candidate: ResearchCandidate,
    *,
    bars: dict[Any, list[Any]],
    instruments: list[Instrument],
    cache: OrchestrationCache,
    snapshot: DatasetSnapshot,
    seed: int,
) -> tuple[CandidateOutcome, BacktestResult]:
    key = config_hash(
        {
            "snapshot": snapshot.identity_hash(),
            "candidate": candidate.identity_hash(),
            "seed": seed,
            "package": __version__,
        }
    )
    cached = cache.get(key)
    if cached is not None:
        outcome, result = cached
        outcome.cached = True
        return outcome, result
    firewall = RiskFirewall(RiskLimits(max_name_weight=0.55, max_names=5, max_gross=1.05))
    firewall.register_instruments(instruments)
    strategy = _strategy_for(candidate)
    lookback = candidate.lookback if candidate.strategy_id != "equal_weight" else 2
    result = run_backtest(
        bars,
        strategy,
        firewall,
        BacktestConfig(lookback=lookback, cost_bps=candidate.cost_bps, seed=seed),
    )
    returns = _period_returns(result.equity_curve)
    p_value = sign_flip_p_value(returns, n_perm=31, seed=seed)
    payload = candidate.model_dump()
    payload.update(
        {
            "total_return": result.total_return,
            "sharpe": result.metrics.get("sharpe"),
            "max_drawdown": result.max_drawdown,
            "p_value": p_value,
            "config_hash": result.config_hash,
            "failed": False,
        }
    )
    outcome = CandidateOutcome.model_validate(payload)
    cache.put(key, (outcome, result))
    return outcome, result


def _baseline_candidate(spec: ResearchSpec) -> ResearchCandidate:
    return ResearchCandidate(
        candidate_id=f"{spec.search_space_id}:baseline:equal_weight",
        search_space_id=spec.search_space_id,
        lookback=spec.lookback,
        top_n=spec.top_n,
        cost_bps=spec.cost_bps,
        strategy_id="equal_weight",
        experiment_type=ExperimentType.DISCOVERY,
        parameters={"baseline": "equal_weight"},
    )


def _falsifier_candidate(spec: ResearchSpec) -> ResearchCandidate:
    return ResearchCandidate(
        candidate_id=f"{spec.search_space_id}:falsify:inverted",
        search_space_id=spec.search_space_id,
        lookback=spec.lookback,
        top_n=spec.top_n,
        cost_bps=spec.cost_bps,
        strategy_id="cs_momentum_inverted",
        experiment_type=ExperimentType.FALSIFICATION,
        parameters={"falsifier": "sign_reversal"},
    )


def _merge_leaks(
    flags: OrchestrationLeakFlags,
    *,
    hidden: bool,
    hidden_failed: bool,
    hidden_search: bool,
    mt_omitted: bool,
    truncated: bool,
    snapshot_mismatch: bool,
    identity_mutated: bool,
    config_mutated: bool,
    posthoc: bool,
    overwrite: bool,
    lineage_broken: bool,
    budget_bypass: bool,
    family_mutated: bool,
    holdout: bool,
    future_selection: bool,
) -> OrchestrationLeakFlags:
    data = flags.model_dump()
    computed = {
        "hidden_candidate": hidden,
        "hidden_failed_experiment": hidden_failed,
        "hidden_search": hidden_search,
        "multiple_testing_omission": mt_omitted,
        "dataset_snapshot_mismatch": snapshot_mismatch,
        "experiment_identity_mutation": identity_mutated,
        "experiment_config_mutation": config_mutated,
        "posthoc_stopping": posthoc,
        "result_overwrite": overwrite,
        "lineage_break": lineage_broken,
        "research_budget_bypass": budget_bypass,
        "family_definition_mutation": family_mutated,
        "holdout_reuse": holdout,
        "future_candidate_selection": future_selection,
        "future_experiment_selection": future_selection,
        "future_hypothesis_selection": False,
        "future_baseline_selection": False,
        "future_model_selection": False,
        "future_execution_selection": False,
        "future_cost_selection": False,
        "replication_contamination": False,
        "parallel_state_leak": False,
        "adaptive_state_cross_contamination": False,
    }
    for name, value in computed.items():
        if data.get(name) is None or data[name] is False:
            data[name] = value
        else:
            data[name] = bool(data[name]) or value
    if truncated and data.get("research_budget_bypass") is None:
        data["research_budget_bypass"] = False
    return OrchestrationLeakFlags(**data)


def execute_spec(
    spec: ResearchSpec,
    *,
    frozen: ResearchSpec | None = None,
    ledger_path: Path,
    fabric_root: Path | None = None,
    append: bool = False,
    leaks: OrchestrationLeakFlags | None = None,
    budget: ResearchBudget | None = None,
    registry: OrchestrationRegistry | None = None,
    hide_failures: bool = False,
    execution_order: list[int] | None = None,
    include_falsification: bool = True,
    include_execution: bool = True,
) -> tuple[OrchestrationReport, ExperimentRun]:
    flags = leaks or OrchestrationLeakFlags()
    store = registry or default_registry()
    cap = budget or ResearchBudget()
    original = frozen or spec
    identity_mutated = original.identity_hash() != spec.identity_hash()

    from quantlab.research.pipeline import load_synthetic_frame

    frame = load_synthetic_frame(
        n_days=spec.n_days, ledger_path=ledger_path, fabric_root=fabric_root
    )
    snapshot = pin_from_frame(frame)
    snapshot_mismatch = bool(spec.snapshot_id) and spec.snapshot_id != snapshot.snapshot_id
    family = store.get_family(spec.family_id)
    family_mutated = family.hypothesis_id != spec.hypothesis_id
    space = store.get_search_space(spec.search_space_id)
    hypothesis = store.get_hypothesis(spec.hypothesis_id)
    generated = expand_grid(space)
    allowed, truncated = apply_budget(len(generated), cap, bypass=False)
    if flags.research_budget_bypass:
        allowed = len(generated)
        truncated = False
    planned = generated[:allowed]
    planned.append(_baseline_candidate(spec))
    if include_falsification:
        planned.append(_falsifier_candidate(spec))
    hidden = any(c.hidden for c in planned) or bool(flags.hidden_candidate)
    rule = StoppingRule(
        policy=spec.stopping_policy,
        max_candidates=cap.max_candidates + 2,
        frozen=True,
    )
    posthoc = bool(flags.posthoc_stopping)
    if not posthoc:
        assert_not_posthoc(rule, mutated_after_results=False)

    cache = OrchestrationCache()

    def _one(candidate: ResearchCandidate) -> tuple[CandidateOutcome, BacktestResult]:
        return _run_candidate(
            candidate,
            bars=frame.bars,
            instruments=frame.instruments,
            cache=cache,
            snapshot=snapshot,
            seed=spec.seed,
        )

    ordered = run_isolated(planned, _one, order=execution_order)
    outcomes = [pair[0] for pair in ordered]
    results = {pair[0].candidate_id: pair[1] for pair in ordered}
    if hide_failures:
        flags = flags.model_copy(update={"hidden_failed_experiment": True})
        outcomes = [item for item in outcomes if not item.failed]
    selected = select_primary(outcomes, spec)
    p_values = [item.p_value for item in outcomes if item.p_value is not None]
    mt_omitted = bool(flags.multiple_testing_omission)
    mt = family_correction(
        p_values,
        method=spec.multiple_testing_method,
        omit=mt_omitted,
    )
    primary_ret = None if selected is None else selected.total_return
    inverted = next((o for o in outcomes if o.strategy_id == "cs_momentum_inverted"), None)
    cost20 = next(
        (
            o
            for o in outcomes
            if o.lookback == spec.lookback
            and abs(o.cost_bps - 20.0) < 1e-12
            and o.strategy_id == "cs_momentum_v1"
        ),
        None,
    )
    fals = falsification_summary(
        primary_return=primary_ret,
        inverted_return=None if inverted is None else inverted.total_return,
        cost_stress_return=None if cost20 is None else cost20.total_return,
    )
    exec_cost: float | None = None
    if include_execution:
        definition = get_execution_model(spec.execution_model_id)
        sim = simulate_execution(
            definition, frame.bars, capital=1_000_000.0, lookback=spec.lookback
        )
        exec_cost = sim.total_cost

    feature = get_feature("momentum_20")
    alpha = get_alpha(spec.alpha_id) if spec.alpha_id else None
    portfolio = get_portfolio_model(spec.portfolio_id)
    _ = (feature, alpha, portfolio)

    bars_flat = [bar for series in frame.bars.values() for bar in series]
    as_of_times = []
    primary_result: BacktestResult | None = None
    if selected is not None:
        primary_result = results.get(selected.candidate_id)
        if primary_result is not None:
            as_of_times = list(primary_result.dates)
    merged = _merge_leaks(
        flags,
        hidden=hidden,
        hidden_failed=bool(flags.hidden_failed_experiment),
        hidden_search=bool(flags.hidden_search),
        mt_omitted=mt_omitted,
        truncated=truncated,
        snapshot_mismatch=snapshot_mismatch,
        identity_mutated=identity_mutated,
        config_mutated=identity_mutated,
        posthoc=posthoc,
        overwrite=bool(flags.result_overwrite),
        lineage_broken=bool(flags.lineage_break),
        budget_bypass=bool(flags.research_budget_bypass),
        family_mutated=family_mutated,
        holdout=bool(flags.holdout_reuse),
        future_selection=spec.selection_policy.value == "max_sharpe",
    )
    integrity = evaluate_integrity(
        bars=bars_flat,
        states=[],
        as_of_times=as_of_times or [bars_flat[-1].pit.event_time],
        next_bar_fill=True,
        cost_bps=spec.cost_bps,
        slippage_model="none",
        live_trading=LiveSafetyGates().live_trading,
        n_experiments_in_family=len(outcomes),
        used_ml=False,
        data_kind=snapshot.data_kind,
        pit_query_verified=True,
        test_used_for_selection=bool(merged.holdout_reuse),
        future_parameter_selection=merged.future_candidate_selection,
        experiment_identity_mutation=merged.experiment_identity_mutation,
        experiment_config_mutation=merged.experiment_config_mutation,
        future_experiment_selection=merged.future_experiment_selection,
        future_candidate_selection=merged.future_candidate_selection,
        future_hypothesis_selection=merged.future_hypothesis_selection,
        hidden_candidate=merged.hidden_candidate,
        hidden_failed_experiment=merged.hidden_failed_experiment,
        hidden_search=merged.hidden_search,
        posthoc_stopping=merged.posthoc_stopping,
        multiple_testing_omission=merged.multiple_testing_omission,
        family_definition_mutation=merged.family_definition_mutation,
        research_budget_bypass=merged.research_budget_bypass,
        replication_contamination=merged.replication_contamination,
        holdout_reuse=merged.holdout_reuse,
        future_baseline_selection=merged.future_baseline_selection,
        future_model_selection=merged.future_model_selection,
        future_execution_selection=merged.future_execution_selection,
        future_cost_selection=merged.future_cost_selection,
        lineage_break=merged.lineage_break,
        dataset_snapshot_mismatch=merged.dataset_snapshot_mismatch,
        result_overwrite=merged.result_overwrite,
        parallel_state_leak=merged.parallel_state_leak,
        adaptive_state_cross_contamination=merged.adaptive_state_cross_contamination,
    )
    graph = build_graph(
        hypothesis_id=spec.hypothesis_id,
        family_id=spec.family_id,
        candidate_ids=[o.candidate_id for o in outcomes],
        parent_experiment=spec.experiment_id,
    )
    if not merged.lineage_break:
        assert_lineage_intact(graph)
    oos_sharpe = None if selected is None else selected.sharpe
    gate = evaluate_research_gate(
        integrity_failed=integrity.failed(),
        next_bar_fill=True,
        cost_bps=spec.cost_bps,
        data_kind=snapshot.data_kind,
        walk_forward_windows=max(len(as_of_times), 1),
        oos_sharpe=oos_sharpe,
        cost_still_positive_at_20bps=None
        if cost20 is None or cost20.total_return is None
        else cost20.total_return > 0,
        parameter_fragile=False,
        statistical_status=mt.status if p_values else CheckResult.WARN,
        n_hypotheses=len(outcomes),
        test_used_for_selection=bool(merged.holdout_reuse),
    )
    dof = degrees_of_freedom(
        family,
        space,
        tested_count=len(outcomes),
        hidden_count=0,
    )
    not_tested = [name for name, value in integrity.as_str_map().items() if value == "not_tested"]
    quality = ResearchQuality.EXPLORATORY
    if fals.hypothesis_survived is False:
        quality = ResearchQuality.FALSIFIED
    elif gate.outcome is GateOutcome.REJECT:
        quality = ResearchQuality.WEAK
    discovery = summarize_discovery(spec.hypothesis_id, spec.family_id, outcomes)
    discovery.quality = quality
    status = ResearchStatus.COMPLETED
    if integrity.failed() or gate.outcome is GateOutcome.REJECT:
        status = ResearchStatus.FAILED
    if quality is ResearchQuality.FALSIFIED:
        status = ResearchStatus.FALSIFIED
    report = OrchestrationReport(
        hypothesis_id=spec.hypothesis_id,
        hypothesis_title=hypothesis.title,
        experiment_id=spec.experiment_id,
        family_id=spec.family_id,
        dataset_id=snapshot.dataset_id,
        snapshot_id=snapshot.snapshot_id,
        data_kind=snapshot.data_kind,
        pit_integrity=integrity.as_str_map(),
        candidate_space=spec.search_space_id,
        candidates=outcomes,
        discovery=discovery,
        comparison=compare_candidates(outcomes),
        ablation=ablating_lookback(outcomes, cost_bps=spec.cost_bps),
        falsification=fals,
        sensitivity=cost_sensitivity(outcomes, lookback=spec.lookback),
        robustness=robustness_summary(outcomes),
        multiple_testing=mt,
        degrees_of_freedom=dof,
        pareto=pareto_front(outcomes),
        lineage=graph,
        gate=gate,
        status=status,
        quality=quality,
        selected_candidate="" if selected is None else selected.candidate_id,
        baseline_id=spec.baseline_id,
        execution_model_id=spec.execution_model_id,
        execution_cost=exec_cost,
        truncated_by_budget=truncated,
        identity_hash=spec.identity_hash(),
        config_hash=spec.config_hash(),
        not_tested=not_tested,
        conclusion=report_conclusion(status, gate.outcome.value, snapshot.data_kind),
    )
    family_run = _ledger_row(
        spec,
        report,
        snapshot,
        family_size=len(outcomes),
        candidate=selected,
        research_type=spec.experiment_type.value,
    )
    if append:
        ledger = ExperimentLedger(ledger_path)
        ledger.append(family_run)
        for item in outcomes:
            child = _ledger_row(
                spec,
                report,
                snapshot,
                family_size=len(outcomes),
                candidate=item,
                research_type=item.experiment_type.value,
                parent_id=family_run.id,
            )
            item.ledger_id = child.id
            ledger.append(child)
        _write_artifacts(ledger_path.parent / "artifacts", family_run, report)
    return report, family_run


def report_conclusion(status: ResearchStatus, gate: str, data_kind: str) -> str:
    return (
        f"Orchestration status={status.value}; gate={gate}; data_kind={data_kind}. "
        "This is a scientific record, not a live strategy."
    )


def _ledger_row(
    spec: ResearchSpec,
    report: OrchestrationReport,
    snapshot: DatasetSnapshot,
    *,
    family_size: int,
    candidate: CandidateOutcome | None,
    research_type: str,
    parent_id: str = "",
) -> ExperimentRun:
    env = environment()
    metrics: dict[str, float] = {}
    if candidate is not None:
        if candidate.total_return is not None:
            metrics["total_return"] = candidate.total_return
        if candidate.sharpe is not None:
            metrics["sharpe"] = candidate.sharpe
        if candidate.max_drawdown is not None:
            metrics["max_drawdown"] = candidate.max_drawdown
        if candidate.p_value is not None:
            metrics["p_value"] = candidate.p_value
    if report.execution_cost is not None:
        metrics["execution_cost"] = report.execution_cost
    status = (
        ExperimentStatus.FAILED
        if report.status is ResearchStatus.FAILED
        else ExperimentStatus.PASSED
    )
    if report.status is ResearchStatus.FALSIFIED:
        status = ExperimentStatus.FAILED
    lookback = spec.lookback if candidate is None else candidate.lookback
    cost = spec.cost_bps if candidate is None else candidate.cost_bps
    cid = "" if candidate is None else candidate.candidate_id
    lineage = DataLineage(
        provider="orchestration",
        dataset_version=snapshot.dataset_version,
        ingested_at=datetime.now(tz=UTC),
        transformations=["research_control_plane", spec.search_space_id],
        feature_versions={"momentum": "seed"},
        signal_version="cs_momentum_v1",
        dataset_id=snapshot.dataset_id,
        snapshot_id=snapshot.snapshot_id,
        data_kind=snapshot.data_kind,
        checksum=snapshot.checksum,
        source="orchestration",
    )
    return ExperimentRun(
        id=str(ExperimentId()),
        name=f"orchestration:{spec.experiment_id}:{cid or 'family'}",
        hypothesis=report.hypothesis_title,
        status=status,
        git_commit=git_commit(),
        dataset_version=snapshot.dataset_version,
        universe=list(spec.universe),
        feature_versions={"momentum": "1"},
        label_definition=spec.label_id,
        hyperparameters={
            "lookback": lookback,
            "top_n": spec.top_n if candidate is None else candidate.top_n,
            "cost_bps": cost,
            "experiment_id": spec.experiment_id,
            "experiment_version": spec.experiment_version,
            "candidate_id": cid,
        },
        transaction_cost_bps=cost,
        slippage_model="none",
        random_seed=spec.seed,
        hypothesis_id=spec.hypothesis_id,
        alpha_id=spec.alpha_id,
        dataset_id=snapshot.dataset_id,
        snapshot_id=snapshot.snapshot_id,
        data_kind=snapshot.data_kind,
        lineage=lineage.as_dict(),
        metrics=metrics,
        integrity=report.pit_integrity,
        application_version=__version__,
        conclusion=report.conclusion,
        config_hash=report.config_hash
        if candidate is None
        else (candidate.config_hash or report.config_hash),
        research_family_id=spec.family_id,
        parent_experiment_id=parent_id,
        n_hypotheses_in_family=family_size,
        selection_stage="orchestration",
        gate_outcome=report.gate.outcome.value,
        gate_reasons=report.gate.as_str_map(),
        validation_protocol=spec.validation_protocol,
        git_dirty=git_dirty(),
        python_version=env.get("python", ""),
        feature_id=spec.feature_ids[0] if spec.feature_ids else "",
        portfolio_id=spec.portfolio_id,
        ensemble_id=spec.ensemble_id,
        risk_model_id=spec.risk_model_id,
        candidate_count=len(report.candidates),
        strategy_id="" if candidate is None else candidate.strategy_id,
        execution_model_id=spec.execution_model_id,
        research_type=research_type,
        search_space_id=spec.search_space_id,
        tested_count=len(report.candidates),
        selection_policy=spec.selection_policy.value,
        stopping_policy=spec.stopping_policy.value,
        multiple_testing_method=spec.multiple_testing_method,
        baseline_id=spec.baseline_id,
        orchestration_id=spec.experiment_id,
        hypothesis_version=spec.hypothesis_version,
    )


def _write_artifacts(root: Path, run: ExperimentRun, report: OrchestrationReport) -> None:
    folder = root / run.id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "orchestration.json").write_text(
        report.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    (folder / "narrative.txt").write_text(report.as_narrative() + "\n", encoding="utf-8")
