"""Shared constructed reports for knowledge tests. Avoid running GP."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.discovery.definitions import CandidateStatus, NoveltyClass, SearchMode
from quantlab.discovery.expression import ExprNode, feature_node, unary
from quantlab.discovery.population import DiscoveryCandidate
from quantlab.discovery.report import DiscoveryReport
from quantlab.domain.models import OHLCVBar
from quantlab.domain.research import CheckResult
from quantlab.orchestration.ablation import AblationReport
from quantlab.orchestration.comparison import ComparisonReport
from quantlab.orchestration.contracts import ResearchStatus
from quantlab.orchestration.discovery import DiscoverySummary
from quantlab.orchestration.falsification import FalsificationReport
from quantlab.orchestration.family import DegreesOfFreedom
from quantlab.orchestration.lineage import ResearchGraph
from quantlab.orchestration.pareto import ParetoReport
from quantlab.orchestration.report import OrchestrationReport
from quantlab.orchestration.robustness import RobustnessReport
from quantlab.orchestration.selection import CandidateOutcome
from quantlab.orchestration.sensitivity import SensitivityReport
from quantlab.research.gate import GateOutcome, ResearchGateResult
from quantlab.research.integrity import evaluate_integrity
from quantlab.research.multiple_testing import MultipleTestingReport


def feature(name: str) -> ExprNode:
    return feature_node(name)


def ranked_momentum() -> ExprNode:
    return unary("rank", feature_node("momentum_20"))


def discovery_candidate(
    *,
    candidate_id: str,
    expr: ExprNode,
    status: CandidateStatus = CandidateStatus.EVALUATED,
    parents: list[str] | None = None,
    mutation: str = "",
) -> DiscoveryCandidate:
    return DiscoveryCandidate(
        candidate_id=candidate_id,
        expression=expr,
        expression_hash=expr.identity_hash(),
        canonical_text=expr.canonical_text(),
        generation=0,
        parents=parents or [],
        origin=SearchMode.SEEDED,
        status=status,
        novelty=NoveltyClass.NOVEL,
        mutation=mutation,
        note="constructed",
    )


def discovery_report(
    *,
    hidden: bool = False,
    include_dead_end: bool = True,
    data_kind: str = "synthetic",
    run_id: str = "DR-TEST-001",
) -> DiscoveryReport:
    elite = ranked_momentum()
    candidates = [discovery_candidate(candidate_id="cand-elite", expr=elite)]
    if include_dead_end:
        dead = unary("rank", feature_node("rolling_std_20"))
        candidates.append(
            discovery_candidate(
                candidate_id="cand-dead",
                expr=dead,
                status=CandidateStatus.FALSIFIED,
                parents=[elite.identity_hash()],
                mutation="mutate",
            )
        )
    return DiscoveryReport(
        family_id="GP-MOM-VOL-001",
        discovery_run_id=run_id,
        grammar_version="1",
        snapshot_id="SNAP-TEST",
        data_kind=data_kind,
        tested_count=len(candidates),
        hidden=hidden,
        elite_text=elite.canonical_text(),
        elite_hash=elite.identity_hash(),
        train_ic=0.02,
        candidates=candidates,
        discovery_status="explored",
    )


def orchestration_report(*, hidden_candidate: bool = False) -> OrchestrationReport:
    cand = CandidateOutcome(
        candidate_id="cell-001",
        search_space_id="ss-mom",
        failed=False,
        hidden=hidden_candidate,
    )
    return OrchestrationReport(
        hypothesis_id="H-MOM-001",
        hypothesis_title="Momentum continuation",
        experiment_id="EXP-MOM-001",
        family_id="MOM-FAMILY-001",
        dataset_id="synthetic",
        snapshot_id="SNAP-ORCH",
        candidate_space="ss-mom",
        candidates=[cand],
        discovery=DiscoverySummary(
            hypothesis_id="H-MOM-001",
            family_id="MOM-FAMILY-001",
            attempted=1,
            failed=0,
            rejected=0,
            survived_discovery=1,
        ),
        comparison=ComparisonReport(),
        ablation=AblationReport(),
        falsification=FalsificationReport(
            method="sign_reversal",
            primary_return=None,
            falsifier_return=None,
            hypothesis_survived=None,
        ),
        sensitivity=SensitivityReport(),
        robustness=RobustnessReport(
            n_candidates=1,
            n_positive_return=0,
            min_return=None,
            max_return=None,
        ),
        multiple_testing=MultipleTestingReport(n_hypotheses=1, status=CheckResult.NOT_TESTED),
        degrees_of_freedom=DegreesOfFreedom(
            family_id="MOM-FAMILY-001",
            search_cells=4,
            free_parameters=2,
        ),
        pareto=ParetoReport(),
        lineage=ResearchGraph(hypothesis_id="H-MOM-001", family_id="MOM-FAMILY-001"),
        gate=ResearchGateResult(outcome=GateOutcome.WARN),
        status=ResearchStatus.COMPLETED,
        conclusion="Constructed orchestration record.",
    )


def integrity_report(**flags: bool | None):
    day = datetime(2024, 1, 2, tzinfo=UTC)
    pit = PointInTime(event_time=day, effective_time=day, available_time=day, ingestion_time=day)
    bar = OHLCVBar(
        instrument=InstrumentId.parse("NSE:TCS"),
        pit=pit,
        open=10,
        high=11,
        low=9,
        close=10,
    )
    return evaluate_integrity(
        bars=[bar],
        states=[],
        as_of_times=[day],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=False,
        n_experiments_in_family=1,
        used_ml=False,
        **flags,
    )
