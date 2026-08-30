"""Named discovery searches. Generates hypotheses; does not promote or trade."""

from __future__ import annotations

import random
from datetime import UTC, datetime
from pathlib import Path

from quantlab import __version__
from quantlab.core.config import LiveSafetyGates
from quantlab.core.identifiers import ExperimentId, InstrumentId
from quantlab.discovery.archive import CandidateArchive
from quantlab.discovery.complexity import complexity
from quantlab.discovery.constraints import validate_expression
from quantlab.discovery.definitions import CandidateStatus, NoveltyClass, SearchMode
from quantlab.discovery.errors import DiscoveryError
from quantlab.discovery.evaluator import evaluate_expression
from quantlab.discovery.expression import ExprNode
from quantlab.discovery.falsification import falsify_panel
from quantlab.discovery.fitness import score_expression
from quantlab.discovery.generator import random_expression, seed_expressions
from quantlab.discovery.genetic import breed, elite, mutated, tournament
from quantlab.discovery.grammar import GrammarSpec
from quantlab.discovery.integrity import DiscoveryLeakFlags
from quantlab.discovery.lineage import build_lineage
from quantlab.discovery.novelty import novelty_class
from quantlab.discovery.population import DiscoveryCandidate
from quantlab.discovery.redundancy import structural_penalty
from quantlab.discovery.registry import get_family
from quantlab.discovery.report import DiscoveryReport
from quantlab.discovery.reproducibility import replay_identity
from quantlab.discovery.search import SearchBudget, assert_budget_frozen
from quantlab.discovery.symbolic import simplify
from quantlab.discovery.validation import SplitSpec, score_splits, split_dates
from quantlab.domain.models import ExperimentRun, ExperimentStatus, OHLCVBar
from quantlab.domain.research import CheckResult, DataLineage
from quantlab.features.engine import Panel, compute_panel, session_calendar
from quantlab.features.registry import get_feature
from quantlab.labels.definition import forward_return
from quantlab.labels.engine import compute_label_panel
from quantlab.models.registry import ExperimentLedger
from quantlab.orchestration.multiple_testing import family_correction
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.research.gate import evaluate_research_gate
from quantlab.research.integrity import evaluate_integrity
from quantlab.research.pipeline import load_synthetic_frame


def run_named_discovery_search(
    family_id: str = "GP-MOM-VOL-001",
    *,
    ledger_path: Path,
    n_days: int = 80,
    fabric_root: Path | None = None,
    budget: SearchBudget | None = None,
    leaks: DiscoveryLeakFlags | None = None,
    label_panel: Panel | None = None,
    append: bool = True,
) -> tuple[DiscoveryReport, ExperimentRun]:
    family = get_family(family_id)
    used = (budget or family.budget).model_copy()
    frozen = used.model_copy()
    flags = leaks or DiscoveryLeakFlags()
    if flags.posthoc_search_budget:
        used = used.model_copy(update={"n_generations": used.n_generations + 2, "frozen": False})
    else:
        assert_budget_frozen(frozen, used)

    frame = load_synthetic_frame(
        n_days=n_days,
        ledger_path=ledger_path,
        fabric_root=fabric_root or (ledger_path.parent / "fabric"),
    )
    dates = session_calendar(frame.bars)
    splits = split_dates(dates)
    grammar = family.grammar
    feature_panels = _feature_panels(grammar, frame.bars, dates)
    labels = (
        label_panel
        if label_panel is not None
        else compute_label_panel(
            forward_return(1),
            frame.bars,
            dates,
        )
    )
    rng = random.Random(used.seed)
    archive = CandidateArchive()
    cache: dict[str, Panel] = {}
    references = {
        "momentum_20": feature_panels.get("momentum_20", {}),
        "rank_momentum_20": evaluate_expression(
            seed_expressions(grammar)[1],
            feature_panels,
            cache,
        )
        if grammar.allowed_features
        else {},
    }
    selection_dates = (
        splits.holdout
        if flags.holdout_contaminated or flags.test_used_for_selection
        else splits.train
    )
    generated: list[DiscoveryCandidate] = []
    live = list(seed_expressions(grammar))
    while len(live) < used.population_size:
        live.append(random_expression(rng, grammar))

    def consider(
        expr: ExprNode,
        generation: int,
        parents: list[str],
        origin: SearchMode,
        mutation: str = "",
    ) -> None:
        if len(generated) >= used.max_candidates:
            return
        status = CandidateStatus.GENERATED
        note = ""
        try:
            if expr.uses_forbidden_label():
                raise DiscoveryError("label entered a discovery expression")
            validate_expression(expr, grammar)
            expr = simplify(expr)
        except DiscoveryError as exc:
            status = CandidateStatus.INVALID
            note = str(exc)
        cand = DiscoveryCandidate(
            candidate_id=f"cand-{generation:02d}-{len(generated):03d}",
            expression=expr,
            expression_hash=expr.identity_hash(),
            canonical_text=expr.canonical_text(),
            generation=generation,
            parents=parents,
            origin=origin,
            status=status,
            mutation=mutation,
            note=note,
        )
        if status is CandidateStatus.INVALID:
            if not flags.hidden_candidate:
                generated.append(cand)
                archive.add(cand)
            return
        try:
            peers = [
                item.expression for item in generated if item.status is CandidateStatus.EVALUATED
            ]
            red = structural_penalty(expr, peers)
            fit, panel = score_expression(
                expr,
                feature_panels,
                labels,
                selection_dates,
                redundancy_penalty=red,
                cache=cache,
            )
            klass, _corr = novelty_class(expr, panel, references, splits.train, archive.hashes())
            cand = cand.model_copy(
                update={
                    "status": CandidateStatus.EVALUATED
                    if klass is not NoveltyClass.DUPLICATE
                    else CandidateStatus.REDUNDANT,
                    "fitness": fit,
                    "novelty": klass,
                }
            )
        except DiscoveryError as exc:
            cand = cand.model_copy(update={"status": CandidateStatus.INVALID, "note": str(exc)})
        if flags.hidden_candidate and cand.status is not CandidateStatus.EVALUATED:
            return
        generated.append(cand)
        archive.add(cand)

    for expr in live:
        consider(expr, 0, ["seed:library"], SearchMode.SEEDED)
    population = [item for item in generated if item.status is CandidateStatus.EVALUATED]
    n_gens = used.n_generations
    for generation in range(1, n_gens):
        if len(generated) >= used.max_candidates or not population:
            break
        keep = elite(population, used.elite)
        offspring: list[tuple[ExprNode, list[str], str]] = []
        while (
            len(keep) + len(offspring) < used.population_size
            and len(generated) + len(offspring) < used.max_candidates
        ):
            parent = tournament(population, rng, used.tournament_k)
            if rng.random() < 0.45 and len(population) >= 2:
                other = tournament(population, rng, used.tournament_k)
                child_a, child_b, parents = breed(parent, other, rng, grammar)
                offspring.append((child_a, parents, "crossover"))
                offspring.append((child_b, parents, "crossover"))
            else:
                node, op = mutated(parent.expression, rng, grammar)
                offspring.append((node, [parent.expression_hash], op))
        for node, parents, op in offspring:
            origin = SearchMode.GENETIC
            consider(node, generation, parents, origin, op)
        population = [item for item in generated if item.fitness is not None]
        if not population:
            population = [item for item in generated if item.status is CandidateStatus.EVALUATED]

    _assign_pareto(generated)
    scored = [item for item in generated if item.fitness is not None]
    if not generated:
        raise DiscoveryError("search produced no recorded candidates")
    elite_cand = max(
        scored, key=lambda item: item.fitness.scalar if item.fitness else float("-inf")
    )
    if not scored:
        elite_cand = generated[0]
    elite_panel = evaluate_expression(elite_cand.expression, feature_panels, cache)
    val = score_splits(elite_panel, labels, splits)
    if flags.holdout_contaminated or flags.test_used_for_selection:
        val = val.model_copy(update={"holdout_used_for_selection": True})
    fals = falsify_panel(
        elite_panel, labels, splits.validation or splits.train, random.Random(used.seed + 1)
    )
    p_values = [item.fitness.p_value for item in scored if item.fitness is not None]
    mt = family_correction(p_values, method="benjamini_hochberg")
    graph = build_lineage(family.family_id, generated)
    integrity = evaluate_integrity(
        bars=frame.flat,
        states=[],
        as_of_times=dates[: min(5, len(dates))],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=LiveSafetyGates().live_trading,
        n_experiments_in_family=len(generated),
        used_ml=True,
        data_kind="synthetic",
        pit_query_verified=True,
        walk_forward_windows_ok=val.walk_forward_windows > 0,
        embargo_enforced=True,
        purge_applied=True,
        test_used_for_selection=bool(flags.test_used_for_selection or flags.holdout_contaminated),
        label_used_as_feature=flags.label_used_as_feature,
        holdout_contaminated=flags.holdout_contaminated,
        hidden_candidate=flags.hidden_candidate,
        posthoc_stopping=True if flags.posthoc_search_budget else flags.posthoc_stopping,
        holdout_reuse=flags.holdout_reuse,
        future_expression_input=flags.future_expression_input,
        future_candidate_generation=flags.future_candidate_generation,
        future_search_state=flags.future_search_state,
        future_fitness=flags.future_fitness,
        future_selection=flags.future_selection,
        future_mutation=flags.future_mutation,
        future_crossover=flags.future_crossover,
        future_feature=flags.future_feature,
        posthoc_search_budget=flags.posthoc_search_budget,
        search_space_omission=flags.search_space_omission,
        candidate_lineage_break=True if graph.broken() else flags.candidate_lineage_break,
        expression_mutation=flags.expression_mutation,
        future_redundancy=flags.future_redundancy,
        future_novelty=flags.future_novelty,
        future_complexity_selection=flags.future_complexity_selection,
    )
    gate = evaluate_research_gate(
        integrity_failed=integrity.failed(),
        next_bar_fill=True,
        cost_bps=10.0,
        data_kind="synthetic",
        walk_forward_windows=val.walk_forward_windows,
        oos_sharpe=None,
        cost_still_positive_at_20bps=None,
        parameter_fragile=False,
        statistical_status=mt.status,
        n_hypotheses=len(generated),
        test_used_for_selection=bool(flags.test_used_for_selection or flags.holdout_contaminated),
    )
    replay = replay_identity(grammar, frozen, frame.record.version)
    cx = complexity(elite_cand.expression)
    discovery_status = (
        "discovery_survivor"
        if elite_cand.fitness and elite_cand.fitness.predictive_score > 0
        else "falsified"
    )
    if not fals.survived:
        discovery_status = "falsified"
    report = DiscoveryReport(
        family_id=family.family_id,
        discovery_run_id=str(ExperimentId()),
        grammar_version=grammar.version,
        snapshot_id=frame.record.version,
        data_kind="synthetic",
        tested_count=len(generated),
        hidden=bool(flags.hidden_candidate),
        elite_text=elite_cand.canonical_text,
        elite_hash=elite_cand.expression_hash,
        train_ic=val.train_ic,
        validation_ic=val.validation_ic,
        holdout_ic=val.holdout_ic,
        novelty=elite_cand.novelty.value,
        complexity=cx.score,
        candidates=generated,
        lineage=graph,
        multiple_testing=mt,
        gate=gate,
        discovery_status=discovery_status,
        integrity_status=CheckResult.FAIL.value if integrity.failed() else CheckResult.PASS.value,
        validation_status=CheckResult.WARN.value,
        replication_status=CheckResult.NOT_TESTED.value,
        pit_integrity=integrity.as_str_map(),
        not_tested=[
            name for name, value in integrity.checks.items() if value is CheckResult.NOT_TESTED
        ][:12],
        conclusion=(
            f"Discovery {discovery_status}; gate={gate.outcome.value}; "
            f"tested={len(generated)}; elite={elite_cand.canonical_text}. "
            "A discovered expression is not an alpha. Synthetic cannot promote."
        ),
        config_hash=replay.identity,
        live_trading=False,
    )
    run = _ledger_row(family.family_id, report, frame, used, elite_cand, splits)
    if append:
        ExperimentLedger(ledger_path).append(run)
        _write_artifacts(ledger_path.parent / "artifacts", run, report)
    return report, run


def planted_label(feature_panels: dict[str, Panel]) -> Panel:
    """Diagnostic label: 2*momentum_5 - rolling_std_20. Not a market target."""
    mom = feature_panels["momentum_5"]
    vol = feature_panels["rolling_std_20"]
    out: Panel = {}
    for ts in sorted(set(mom) & set(vol)):
        row: dict[str, float] = {}
        for name in set(mom[ts]) & set(vol[ts]):
            row[name] = 2.0 * mom[ts][name] - vol[ts][name]
        if row:
            out[ts] = row
    return out


def random_label(template: Panel, seed: int) -> Panel:
    rng = random.Random(seed)
    out: Panel = {}
    for ts, row in template.items():
        out[ts] = {name: rng.gauss(0.0, 1.0) for name in row}
    return out


def _feature_panels(
    grammar: GrammarSpec,
    bars: dict[InstrumentId, list[OHLCVBar]],
    dates: list[datetime],
) -> dict[str, Panel]:
    panels: dict[str, Panel] = {}
    for feature_id in grammar.allowed_features:
        panels[feature_id] = compute_panel(get_feature(feature_id), bars, as_of_times=dates)
    return panels


def _assign_pareto(candidates: list[DiscoveryCandidate]) -> None:
    scored = [item for item in candidates if item.fitness is not None]
    for item in scored:
        fit = item.fitness
        assert fit is not None
        dominated = False
        for other in scored:
            ofit = other.fitness
            assert ofit is not None
            ge = (
                ofit.predictive_score >= fit.predictive_score
                and ofit.complexity_penalty <= fit.complexity_penalty
            )
            gt = (
                ofit.predictive_score > fit.predictive_score
                or ofit.complexity_penalty < fit.complexity_penalty
            )
            if ge and gt:
                dominated = True
                break
        item.fitness = fit.model_copy(update={"pareto_rank": 2 if dominated else 1})


def _ledger_row(
    family_id: str,
    report: DiscoveryReport,
    frame: object,
    budget: SearchBudget,
    elite_cand: DiscoveryCandidate,
    splits: SplitSpec,
) -> ExperimentRun:
    from quantlab.research.pipeline import SyntheticFrame

    assert isinstance(frame, SyntheticFrame)
    env = environment()
    metrics = {
        "train_ic": float(report.train_ic or 0.0),
        "validation_ic": float(report.validation_ic or 0.0),
        "tested_count": float(report.tested_count),
        "complexity": float(report.complexity),
    }
    lineage = DataLineage(
        provider="discovery",
        dataset_version=frame.record.version,
        ingested_at=datetime.now(tz=UTC),
        transformations=["alpha_discovery", family_id],
        feature_versions={"momentum_20": "1"},
        signal_version="discovery_v1",
        dataset_id=frame.record.dataset_id,
        snapshot_id=frame.record.version,
        data_kind="synthetic",
        checksum=frame.record.checksum,
        source="discovery",
    )
    gate_outcome = report.gate.outcome.value if report.gate else ""
    return ExperimentRun(
        id=report.discovery_run_id,
        name=f"discovery:{family_id}",
        hypothesis="Discovered expressions are hypotheses, not alphas.",
        status=ExperimentStatus.PASSED if not report.hidden else ExperimentStatus.FAILED,
        git_commit=git_commit(),
        dataset_version=frame.record.version,
        universe=[str(inst.id) for inst in frame.instruments],
        feature_versions={"momentum_20": "1"},
        label_definition="forward_return_1",
        hyperparameters={
            "population": budget.population_size,
            "generations": budget.n_generations,
            "max_candidates": budget.max_candidates,
            "family_id": family_id,
        },
        training_period=str(len(splits.train)),
        validation_period=str(len(splits.validation)),
        test_period=str(len(splits.holdout)),
        transaction_cost_bps=10.0,
        random_seed=budget.seed,
        hypothesis_id="H-DISC-001",
        dataset_id=frame.record.dataset_id,
        snapshot_id=frame.record.version,
        data_kind="synthetic",
        lineage=lineage.as_dict(),
        metrics=metrics,
        integrity=report.pit_integrity,
        application_version=__version__,
        conclusion=report.conclusion,
        config_hash=report.config_hash,
        research_family_id=family_id,
        n_hypotheses_in_family=report.tested_count,
        selection_stage="discovery",
        gate_outcome=gate_outcome,
        gate_reasons=report.gate.as_str_map() if report.gate else {},
        git_dirty=git_dirty(),
        python_version=env.get("python", ""),
        candidate_count=report.tested_count,
        research_type="alpha_discovery",
        search_space_id=family_id,
        tested_count=report.tested_count,
        selection_policy="pareto_ic_complexity",
        stopping_policy="frozen_budget",
        multiple_testing_method="benjamini_hochberg",
        discovery_run_id=report.discovery_run_id,
        expression_hash=elite_cand.expression_hash,
        generation=elite_cand.generation,
        complexity_score=report.complexity,
        novelty_class=elite_cand.novelty.value,
        search_family_id=family_id,
        grammar_version=report.grammar_version,
    )


def _write_artifacts(root: Path, run: ExperimentRun, report: DiscoveryReport) -> None:
    folder = root / run.id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "discovery.json").write_text(
        report.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
