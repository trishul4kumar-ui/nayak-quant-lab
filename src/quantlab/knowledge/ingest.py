"""Ingest ledger, discovery, and orchestration records into the knowledge graph."""

from __future__ import annotations

from pathlib import Path

from quantlab.discovery.definitions import CandidateStatus
from quantlab.discovery.report import DiscoveryReport
from quantlab.domain.models import ExperimentRun
from quantlab.domain.research import CheckResult
from quantlab.knowledge.entities import (
    AlphaFamily,
    ClaimStatus,
    ContentOrigin,
    EvidenceRecord,
    EvidenceType,
    HypothesisRecord,
    HypothesisStatus,
    KnowledgeNode,
    NodeType,
    RelationType,
    ResearchClaim,
    SearchAccounting,
)
from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.evidence import add_evidence
from quantlab.knowledge.genealogy import register_hypothesis
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.relationships import relate
from quantlab.knowledge.serialization import load_graph, save_graph
from quantlab.knowledge.status import add_claim
from quantlab.orchestration.report import OrchestrationReport


def _node(
    node_id: str,
    node_type: NodeType,
    *,
    ref_id: str = "",
    status: str = "recorded",
    source: str = "ingest",
    metadata: dict[str, str] | None = None,
) -> KnowledgeNode:
    return KnowledgeNode(
        node_id=node_id,
        node_type=node_type,
        ref_id=ref_id or node_id,
        status=status,
        source=source,
        metadata=metadata or {},
    ).compute_hashes()


def ingest_discovery_report(graph: KnowledgeGraph, report: DiscoveryReport) -> None:
    run_id = f"discovery:{report.discovery_run_id}"
    graph.add_node(
        _node(
            run_id,
            NodeType.DISCOVERY_RUN,
            ref_id=report.discovery_run_id,
            metadata={"family_id": report.family_id, "tested": str(report.tested_count)},
        )
    )
    family_id = f"family:{report.family_id}"
    graph.add_node(_node(family_id, NodeType.ALPHA_FAMILY, ref_id=report.family_id))
    hypo_id = "hypothesis:H-DISC-001"
    graph.add_node(_node(hypo_id, NodeType.HYPOTHESIS, ref_id="H-DISC-001", status="under_test"))
    register_hypothesis(
        graph,
        HypothesisRecord(
            hypothesis_id="H-DISC-001",
            title="Discovered expressions are hypotheses",
            statement="PIT expressions may contain incremental information vs forward return.",
            discovery_id=report.discovery_run_id,
            status=HypothesisStatus.UNDER_TEST,
        ),
    )
    graph.add_edge(relate(run_id, hypo_id, RelationType.PRODUCED_BY))
    hashes: dict[str, str] = {}
    falsified = 0
    rejected = 0
    duplicates = 0
    for cand in report.candidates:
        expr_id = f"expression:{cand.expression_hash}"
        hashes[cand.expression_hash] = expr_id
        graph.add_node(
            _node(
                expr_id,
                NodeType.EXPRESSION,
                ref_id=cand.expression_hash,
                metadata={"text": cand.canonical_text[:200]},
            )
        )
        result_id = f"result:{cand.candidate_id}"
        graph.add_node(
            _node(
                result_id,
                NodeType.RESEARCH_RESULT,
                ref_id=cand.candidate_id,
                status=cand.status.value,
                metadata={
                    "generation": str(cand.generation),
                    "novelty": cand.novelty.value,
                    "mutation": cand.mutation,
                },
            )
        )
        graph.add_edge(relate(result_id, expr_id, RelationType.PRODUCED_BY))
        graph.add_edge(
            relate(
                expr_id, run_id, RelationType.DERIVED_FROM, experiment_id=report.discovery_run_id
            )
        )
        graph.add_edge(relate(expr_id, family_id, RelationType.MEMBER_OF))
        for parent in cand.parents:
            parent_id = hashes.get(parent, f"expression:{parent}")
            if parent_id in graph.node_map():
                rel = (
                    RelationType.CROSSED_FROM
                    if cand.mutation == "crossover"
                    else RelationType.MUTATED_FROM
                )
                if cand.mutation == "simplify":
                    rel = RelationType.SIMPLIFIED_FROM
                graph.add_edge(relate(expr_id, parent_id, rel))
        if cand.status in {CandidateStatus.FALSIFIED, CandidateStatus.INVALID}:
            falsified += 1
            dead_id = f"dead-end:{cand.candidate_id}"
            graph.add_node(
                _node(
                    dead_id,
                    NodeType.DEAD_END,
                    ref_id=cand.candidate_id,
                    status="falsified",
                    metadata={
                        "why": (cand.note or cand.status.value)[:200],
                        "text": cand.canonical_text[:200],
                    },
                )
            )
            graph.add_edge(relate(expr_id, dead_id, RelationType.FALSIFIED_BY))
            fals_id = f"falsification:{cand.candidate_id}"
            graph.add_node(
                _node(
                    fals_id,
                    NodeType.FALSIFICATION,
                    ref_id=cand.candidate_id,
                    status="falsified",
                )
            )
            graph.add_edge(relate(expr_id, fals_id, RelationType.FALSIFIED_BY))
        if cand.status is CandidateStatus.REJECTED:
            rejected += 1
        if cand.status is CandidateStatus.REDUNDANT:
            duplicates += 1
        for feat in cand.expression.feature_names():
            feat_id = f"feature:{feat}"
            graph.add_node(_node(feat_id, NodeType.FEATURE, ref_id=feat))
            graph.add_edge(relate(expr_id, feat_id, RelationType.USES_FEATURE))
    if report.hidden:
        raise KnowledgeError("search_degree_of_freedom_loss: hidden candidates")
    ev = EvidenceRecord(
        evidence_id=f"evidence:{report.discovery_run_id}:train_ic",
        experiment_id=report.discovery_run_id,
        hypothesis_id="H-DISC-001",
        dataset_id=report.snapshot_id,
        snapshot_checksum=report.snapshot_id,
        config_hash=report.config_hash,
        result_type=EvidenceType.DISCOVERY_EVIDENCE,
        metric="train_ic",
        metric_value=report.train_ic,
        integrity_status=CheckResult.WARN if report.data_kind == "synthetic" else CheckResult.PASS,
        gate_status=report.gate.outcome.value if report.gate else "",
        data_kind=report.data_kind,
        limitations=["synthetic data"] if report.data_kind == "synthetic" else [],
    )
    add_evidence(graph, ev)
    evid_node = f"evidence:{ev.evidence_id}"
    graph.add_node(_node(evid_node, NodeType.EVIDENCE, ref_id=ev.evidence_id))
    graph.add_edge(relate(evid_node, hypo_id, RelationType.EVIDENCE_FOR))
    claim_status = (
        ClaimStatus.PRELIMINARY if report.data_kind == "synthetic" else ClaimStatus.SUPPORTED
    )
    add_claim(
        graph,
        ResearchClaim(
            claim_id=f"claim:{report.discovery_run_id}",
            hypothesis_id="H-DISC-001",
            statement=f"Elite {report.elite_text} was recorded under the discovery protocol.",
            support_evidence_ids=[ev.evidence_id],
            dataset_id=report.snapshot_id,
            status=claim_status,
            limitations=ev.limitations,
            knowledge_as_of=report.snapshot_id,
        ),
    )
    graph.accounting.append(
        SearchAccounting(
            family_id=report.family_id,
            search_space_id=report.family_id,
            candidate_count=len(report.candidates),
            tested_count=report.tested_count,
            rejected_count=rejected,
            falsified_count=falsified,
            selected_count=1 if report.elite_hash else 0,
            duplicate_count=duplicates,
            selection_policy="pareto_ic_complexity",
        )
    )
    members = [f"expression:{c.expression_hash}" for c in report.candidates]
    graph.families.append(
        AlphaFamily(
            family_id=report.family_id,
            title="Discovery family",
            member_ids=members,
            failed_members=[
                m
                for m, c in zip(members, report.candidates, strict=False)
                if c.status is CandidateStatus.FALSIFIED
            ],
            surviving_members=[f"expression:{report.elite_hash}"] if report.elite_hash else [],
        )
    )


def ingest_orchestration_report(graph: KnowledgeGraph, report: OrchestrationReport) -> None:
    exp_id = f"experiment:{report.experiment_id}"
    graph.add_node(
        _node(
            exp_id,
            NodeType.EXPERIMENT,
            ref_id=report.experiment_id,
            metadata={"family_id": report.family_id, "tested": str(len(report.candidates))},
        )
    )
    hypo_id = f"hypothesis:{report.hypothesis_id}"
    graph.add_node(
        _node(hypo_id, NodeType.HYPOTHESIS, ref_id=report.hypothesis_id, status=report.status.value)
    )
    register_hypothesis(
        graph,
        HypothesisRecord(
            hypothesis_id=report.hypothesis_id,
            title=report.hypothesis_title,
            statement=report.hypothesis_title,
            pre_registration_id=report.experiment_id,
            status=HypothesisStatus.UNDER_TEST,
        ),
    )
    snap_id = f"snapshot:{report.snapshot_id}"
    graph.add_node(_node(snap_id, NodeType.DATASET_SNAPSHOT, ref_id=report.snapshot_id))
    graph.add_edge(relate(exp_id, hypo_id, RelationType.TESTED_BY))
    graph.add_edge(relate(exp_id, snap_id, RelationType.PRODUCED_BY))
    if any(item.hidden for item in report.candidates):
        raise KnowledgeError("search_degree_of_freedom_loss: hidden orchestration candidates")
    for cand in report.candidates:
        cid = f"experiment-candidate:{cand.candidate_id}"
        graph.add_node(
            _node(
                cid,
                NodeType.RESEARCH_RESULT,
                ref_id=cand.candidate_id,
                status="failed" if cand.failed else "recorded",
            )
        )
        graph.add_edge(
            relate(cid, exp_id, RelationType.DERIVED_FROM, experiment_id=report.experiment_id)
        )
    graph.accounting.append(
        SearchAccounting(
            family_id=report.family_id,
            search_space_id=report.candidate_space,
            candidate_count=len(report.candidates),
            tested_count=len(report.candidates),
            rejected_count=sum(1 for item in report.candidates if item.failed),
            selected_count=1 if report.selected_candidate else 0,
            selection_policy="pre_registered",
        )
    )
    ev = EvidenceRecord(
        evidence_id=f"evidence:orch:{report.experiment_id}",
        experiment_id=report.experiment_id,
        hypothesis_id=report.hypothesis_id,
        dataset_id=report.dataset_id,
        snapshot_checksum=report.snapshot_id,
        config_hash=report.config_hash,
        result_type=EvidenceType.IN_SAMPLE_EVIDENCE,
        metric="gate",
        integrity_status=CheckResult.WARN
        if report.data_kind == "synthetic"
        else CheckResult.NOT_TESTED,
        gate_status=report.gate.outcome.value,
        data_kind=report.data_kind,
        limitations=["synthetic data"] if report.data_kind == "synthetic" else [],
    )
    add_evidence(graph, ev)
    evid_node = f"evidence:{ev.evidence_id}"
    graph.add_node(_node(evid_node, NodeType.EVIDENCE, ref_id=ev.evidence_id))
    graph.add_edge(relate(evid_node, hypo_id, RelationType.EVIDENCE_FOR))
    add_claim(
        graph,
        ResearchClaim(
            claim_id=f"claim:orch:{report.experiment_id}",
            hypothesis_id=report.hypothesis_id,
            statement=report.conclusion or report.as_narrative()[:240],
            support_evidence_ids=[ev.evidence_id],
            dataset_id=report.dataset_id,
            status=ClaimStatus.PRELIMINARY
            if report.data_kind == "synthetic"
            else ClaimStatus.SUPPORTED,
            limitations=ev.limitations,
            knowledge_as_of=report.snapshot_id,
        ),
    )


def ingest_ledger_run(graph: KnowledgeGraph, run: ExperimentRun) -> None:
    node_id = f"experiment:{run.id}"
    graph.add_node(
        _node(
            node_id,
            NodeType.EXPERIMENT,
            ref_id=run.id,
            status=run.status.value,
            metadata={
                "stage": run.selection_stage,
                "gate": run.gate_outcome,
                "data_kind": run.data_kind,
                "tested": str(run.tested_count),
            },
        )
    )
    if run.hypothesis_id:
        hid = f"hypothesis:{run.hypothesis_id}"
        graph.add_node(_node(hid, NodeType.HYPOTHESIS, ref_id=run.hypothesis_id))
        graph.add_edge(relate(node_id, hid, RelationType.TESTED_BY))
    if run.expression_hash:
        eid = f"expression:{run.expression_hash}"
        graph.add_node(_node(eid, NodeType.EXPRESSION, ref_id=run.expression_hash))
        graph.add_edge(relate(eid, node_id, RelationType.PRODUCED_BY))
    ev = EvidenceRecord(
        evidence_id=f"evidence:ledger:{run.id}",
        experiment_id=run.id,
        hypothesis_id=run.hypothesis_id or "",
        dataset_id=run.dataset_id,
        snapshot_checksum=run.snapshot_id,
        config_hash=run.config_hash,
        result_type=EvidenceType.IN_SAMPLE_EVIDENCE,
        metric="gate",
        integrity_status=CheckResult.WARN
        if run.data_kind == "synthetic"
        else CheckResult.NOT_TESTED,
        gate_status=run.gate_outcome,
        data_kind=run.data_kind,
        origin=ContentOrigin.EMPIRICAL,
        limitations=["synthetic data"] if run.data_kind == "synthetic" else [],
    )
    if run.hypothesis_id:
        add_evidence(graph, ev)


def persist_discovery_report(report: DiscoveryReport, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_discovery_report(graph, report)
    save_graph(graph, path)


def persist_orchestration_report(report: OrchestrationReport, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_orchestration_report(graph, report)
    save_graph(graph, path)


def ingest_capital_decision(graph: KnowledgeGraph, decision: object) -> None:
    from quantlab.capital.definitions import InvestmentDecision

    if not isinstance(decision, InvestmentDecision):
        raise KnowledgeError("capital ingest requires an InvestmentDecision")
    policy_id = f"capital-policy:{decision.capital_policy_id}"
    graph.add_node(
        _node(
            policy_id,
            NodeType.CAPITAL_POLICY,
            ref_id=decision.capital_policy_id,
            status="frozen",
            metadata={"hash": decision.config_hash},
        )
    )
    dec_id = f"decision:{decision.decision_id}"
    graph.add_node(
        _node(
            dec_id,
            NodeType.INVESTMENT_DECISION,
            ref_id=decision.decision_id,
            status=decision.decision_status.value,
            metadata={
                "abstention": decision.abstention_code.value,
                "data_kind": decision.data_kind,
                "hash": decision.decision_hash,
            },
        )
    )
    target_id = f"target:{decision.decision_id}"
    graph.add_node(
        _node(
            target_id,
            NodeType.TARGET_PORTFOLIO,
            ref_id=decision.decision_id,
            status=decision.decision_status.value,
            metadata={"gross": str(decision.gross_target)},
        )
    )
    graph.add_edge(relate(dec_id, policy_id, RelationType.PRODUCED_BY))
    graph.add_edge(relate(target_id, dec_id, RelationType.PRODUCED_BY))
    if decision.knowledge_snapshot_id:
        snap = f"snapshot:{decision.knowledge_snapshot_id}"
        if snap not in graph.node_map():
            graph.add_node(
                _node(snap, NodeType.DATASET_SNAPSHOT, ref_id=decision.knowledge_snapshot_id)
            )
        graph.add_edge(relate(dec_id, snap, RelationType.USES_FEATURE, basis="knowledge_snapshot"))
    hypo = "hypothesis:H-MOM-001"
    if hypo not in graph.node_map():
        graph.add_node(_node(hypo, NodeType.HYPOTHESIS, ref_id="H-MOM-001"))
    graph.add_edge(relate(dec_id, hypo, RelationType.TESTED_BY))
    if decision.decision_status.value in {"rejected", "abstain"}:
        dead = f"dead-end:capital-{decision.decision_id}"
        graph.add_node(
            _node(
                dead,
                NodeType.DEAD_END,
                ref_id=decision.decision_id,
                status=decision.decision_status.value,
                metadata={"reason": decision.abstention_reason},
            )
        )
        graph.add_edge(relate(dec_id, dead, RelationType.FALSIFIED_BY, basis="capital_abstention"))


def persist_capital_decision(decision: object, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_capital_decision(graph, decision)
    save_graph(graph, path)


def ingest_paper_oms(graph: KnowledgeGraph, result: object, decision: object) -> None:
    from quantlab.capital.definitions import InvestmentDecision
    from quantlab.paper_oms.models import PaperOMSResult

    if not isinstance(result, PaperOMSResult) or not isinstance(decision, InvestmentDecision):
        raise KnowledgeError("paper ingest requires PaperOMSResult and InvestmentDecision")
    ingest_capital_decision(graph, decision)
    dec_id = f"decision:{decision.decision_id}"
    target_id = f"target:{decision.decision_id}"
    intent_id = f"intent:{result.run.intent_hash or result.run.oms_run_id}"
    graph.add_node(
        _node(
            intent_id,
            NodeType.ORDER_INTENT,
            ref_id=result.run.intent_hash,
            metadata={"n": str(len(result.intents))},
        )
    )
    plan_id = f"plan:{result.plan.order_plan_id}"
    graph.add_node(
        _node(
            plan_id,
            NodeType.ORDER_PLAN,
            ref_id=result.plan.order_plan_id,
            metadata={"hash": result.plan.order_plan_hash},
        )
    )
    graph.add_edge(relate(intent_id, target_id, RelationType.DERIVED_FROM))
    graph.add_edge(relate(plan_id, intent_id, RelationType.DERIVED_FROM))
    for order in result.orders:
        oid = f"paper-order:{order.order_id}"
        graph.add_node(
            _node(
                oid,
                NodeType.PAPER_ORDER,
                ref_id=order.order_id,
                status=order.state.value,
                metadata={"security": order.security_id},
            )
        )
        graph.add_edge(relate(oid, plan_id, RelationType.PRODUCED_BY))
        if order.state.value in {"rejected", "failed", "cancelled"}:
            dead = f"dead-end:paper-{order.order_id}"
            graph.add_node(
                _node(dead, NodeType.DEAD_END, ref_id=order.order_id, status=order.state.value)
            )
            graph.add_edge(relate(oid, dead, RelationType.FALSIFIED_BY, basis="paper_order"))
    for fill in result.fills:
        fid = f"paper-fill:{fill.fill_id}"
        graph.add_node(
            _node(
                fid,
                NodeType.PAPER_FILL,
                ref_id=fill.fill_id,
                metadata={"note": "simulated; not broker-confirmed"},
            )
        )
        graph.add_edge(relate(fid, f"paper-order:{fill.order_id}", RelationType.PRODUCED_BY))
    rec_id = f"recon:{result.reconciliation.report_id}"
    graph.add_node(
        _node(
            rec_id,
            NodeType.RECONCILIATION,
            ref_id=result.reconciliation.report_id,
            status=result.reconciliation.status.value,
            metadata={"breaks": ",".join(result.reconciliation.breaks)},
        )
    )
    graph.add_edge(relate(rec_id, plan_id, RelationType.TESTED_BY))
    graph.add_edge(relate(rec_id, dec_id, RelationType.EVIDENCE_FOR))
    if result.reconciliation.status.value == "reconciliation_break":
        dead = f"dead-end:recon-{result.run.oms_run_id}"
        graph.add_node(_node(dead, NodeType.DEAD_END, ref_id=result.run.oms_run_id, status="break"))
        graph.add_edge(relate(rec_id, dead, RelationType.FALSIFIED_BY, basis="reconciliation"))


def persist_paper_oms(result: object, decision: object, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_paper_oms(graph, result, decision)
    save_graph(graph, path)


def ingest_monitoring(graph: KnowledgeGraph, result: object, decision: object) -> None:
    from quantlab.capital.definitions import InvestmentDecision
    from quantlab.monitoring.models import MonitoringResult

    if not isinstance(result, MonitoringResult) or not isinstance(decision, InvestmentDecision):
        raise KnowledgeError("monitoring ingest requires MonitoringResult and InvestmentDecision")
    ingest_capital_decision(graph, decision)
    run_id = f"performance:{result.run.monitoring_run_id}"
    graph.add_node(
        _node(
            run_id,
            NodeType.PERFORMANCE_RUN,
            ref_id=result.run.monitoring_run_id,
            metadata={"hash": result.run.run_hash, "pnl": str(result.pnl.pnl_total)},
        )
    )
    obs_id = f"perf-obs:{result.snapshot.snapshot_id}"
    graph.add_node(
        _node(
            obs_id,
            NodeType.PERFORMANCE_OBSERVATION,
            ref_id=result.snapshot.snapshot_id,
            metadata={"equity": str(result.snapshot.equity.equity)},
        )
    )
    attr_id = f"attr:{result.run.attribution_hash[:16]}"
    graph.add_node(
        _node(
            attr_id,
            NodeType.ATTRIBUTION_RESULT,
            ref_id=result.run.attribution_hash,
            status=result.attribution.method.value,
        )
    )
    risk_id = f"risk-obs:{result.run.monitoring_run_id}"
    graph.add_node(_node(risk_id, NodeType.RISK_OBSERVATION, ref_id=result.run.monitoring_run_id))
    drift_id = f"drift:{result.run.monitoring_run_id}"
    graph.add_node(
        _node(
            drift_id,
            NodeType.DRIFT_OBSERVATION,
            ref_id=result.run.monitoring_run_id,
            status=result.drift.status.value,
        )
    )
    graph.add_edge(relate(obs_id, run_id, RelationType.PRODUCED_BY))
    graph.add_edge(relate(attr_id, run_id, RelationType.DERIVED_FROM))
    graph.add_edge(relate(run_id, f"decision:{decision.decision_id}", RelationType.EVIDENCE_FOR))
    for item in result.feedback:
        fid = f"feedback:{item.feedback_id}"
        graph.add_node(
            _node(
                fid,
                NodeType.RESEARCH_FEEDBACK,
                ref_id=item.feedback_id,
                status=item.kind.value,
                metadata={"hypothesis": "false"},
            )
        )
        graph.add_edge(relate(fid, run_id, RelationType.DERIVED_FROM))
        if item.kind.value in {"unexplained", "insufficient_evidence"}:
            dead = f"dead-end:feedback-{item.feedback_id}"
            graph.add_node(
                _node(
                    dead,
                    NodeType.DEAD_END,
                    ref_id=item.feedback_id,
                    status=item.kind.value,
                )
            )
            graph.add_edge(relate(fid, dead, RelationType.FALSIFIED_BY, basis="monitoring"))


def persist_monitoring(result: object, decision: object, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_monitoring(graph, result, decision)
    save_graph(graph, path)


def ingest_tca(graph: KnowledgeGraph, result: object) -> None:
    from quantlab.tca.models import TCAResult

    if not isinstance(result, TCAResult):
        raise KnowledgeError("tca ingest requires TCAResult")
    run_id = f"tca:{result.run.tca_run_id}"
    graph.add_node(
        _node(
            run_id,
            NodeType.TCA_RUN,
            ref_id=result.run.tca_run_id,
            metadata={"kind": result.kind.value, "hash": result.run.tca_hash},
        )
    )
    graph.add_node(
        _node(
            f"exec-obs:{result.run.tca_run_id}",
            NodeType.EXECUTION_OBSERVATION,
            ref_id=result.run.tca_run_id,
        )
    )
    if result.calibration is not None:
        cal_id = f"calib:{result.calibration.model_id}"
        graph.add_node(
            _node(
                cal_id,
                NodeType.CALIBRATED_EXECUTION_MODEL,
                ref_id=result.calibration.model_id,
                metadata={"version": result.calibration.model_version},
            )
        )
        graph.add_edge(relate(cal_id, run_id, RelationType.DERIVED_FROM))
    graph.add_node(
        _node(
            f"liq:{result.run.tca_run_id}",
            NodeType.LIQUIDITY_OBSERVATION,
            ref_id=result.run.tca_run_id,
        )
    )
    cap_id = f"capacity:{result.run.tca_run_id}"
    graph.add_node(
        _node(
            cap_id,
            NodeType.CAPACITY_RESULT,
            ref_id=result.run.tca_run_id,
            status=result.capacity.status.value,
        )
    )
    frag_id = f"fragility:{result.run.tca_run_id}"
    graph.add_node(
        _node(
            frag_id,
            NodeType.FRAGILITY_RESULT,
            ref_id=result.run.tca_run_id,
            status=result.fragility.status.value,
        )
    )
    graph.add_edge(relate(cap_id, run_id, RelationType.DERIVED_FROM))
    graph.add_edge(relate(frag_id, run_id, RelationType.DERIVED_FROM))
    cap_bad = result.capacity.status.value in {"breach", "not_tested"}
    frag_bad = result.fragility.status.value in {
        "fragile",
        "economically_unviable",
    }
    if cap_bad or frag_bad:
        dead = f"dead-end:tca-{result.run.tca_run_id}"
        graph.add_node(_node(dead, NodeType.DEAD_END, ref_id=result.run.tca_run_id, status="tca"))
        graph.add_edge(relate(run_id, dead, RelationType.FALSIFIED_BY, basis="tca"))


def persist_tca(result: object, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_tca(graph, result)
    save_graph(graph, path)


def ingest_econometrics(graph: KnowledgeGraph, result: object) -> None:
    from quantlab.econometrics.models import EconometricResult

    if not isinstance(result, EconometricResult):
        raise KnowledgeError("econometrics ingest requires EconometricResult")
    run_id = f"econo:{result.run.econometrics_run_id}"
    graph.add_node(
        _node(
            run_id,
            NodeType.ECONOMETRIC_RUN,
            ref_id=result.run.econometrics_run_id,
            metadata={"hash": result.run.run_hash, "spec": result.spec.spec_id},
        )
    )
    est_id = f"econo-est:{result.spec.spec_id}"
    graph.add_node(
        _node(
            est_id,
            NodeType.ECONOMETRIC_ESTIMATE,
            ref_id=result.spec.spec_id,
            status=result.spec.estimator.value,
        )
    )
    graph.add_edge(relate(est_id, run_id, RelationType.PRODUCED_BY))
    for item in result.diagnostics.stationarity:
        sid = f"stationarity:{result.run.econometrics_run_id}:{item.method}"
        graph.add_node(
            _node(
                sid,
                NodeType.STATIONARITY_TEST,
                ref_id=item.method,
                status=item.status.value,
            )
        )
        graph.add_edge(relate(sid, run_id, RelationType.DERIVED_FROM))
    if result.diagnostics.cointegration is not None:
        cid = f"coint:{result.run.econometrics_run_id}"
        graph.add_node(
            _node(
                cid,
                NodeType.COINTEGRATION_TEST,
                ref_id=result.diagnostics.cointegration.method.value,
                status=result.diagnostics.cointegration.status.value,
            )
        )
        graph.add_edge(relate(cid, run_id, RelationType.DERIVED_FROM))
    if result.diagnostics.breaks is not None:
        bid = f"break:{result.run.econometrics_run_id}"
        graph.add_node(
            _node(
                bid,
                NodeType.STRUCTURAL_BREAK,
                ref_id=result.diagnostics.breaks.kind.value,
                status=result.diagnostics.breaks.status.value,
            )
        )
        graph.add_edge(relate(bid, run_id, RelationType.DERIVED_FROM))
    if result.causal is not None:
        hid = f"causal:{result.causal.hypothesis_id}"
        graph.add_node(
            _node(
                hid,
                NodeType.CAUSAL_HYPOTHESIS,
                ref_id=result.causal.hypothesis_id,
                status=result.causal.claim.value,
                metadata={"note": "assumptions explicit; not proof of causation"},
            )
        )
        graph.add_edge(relate(hid, run_id, RelationType.EVIDENCE_FOR))


def persist_econometrics(result: object, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_econometrics(graph, result)
    save_graph(graph, path)


def ingest_certification(graph: KnowledgeGraph, result: object) -> None:
    from quantlab.certification.models import CertificationResult

    if not isinstance(result, CertificationResult):
        raise KnowledgeError("certification ingest requires CertificationResult")
    cand_id = f"candidate:{result.candidate.candidate_id}"
    graph.add_node(
        _node(
            cand_id,
            NodeType.CERTIFICATION_CANDIDATE,
            ref_id=result.candidate.candidate_id,
            status=result.state.value,
            metadata={"hash": result.run.spec_hash},
        )
    )
    val_id = f"validation-run:{result.run.certification_id}"
    graph.add_node(
        _node(
            val_id,
            NodeType.VALIDATION_RUN,
            ref_id=result.run.certification_id,
            status=result.state.value,
            metadata={"checklist": result.run.checklist_hash},
        )
    )
    graph.add_edge(relate(val_id, cand_id, RelationType.TESTED_BY))
    dec_id = f"cert-decision:{result.run.certification_id}"
    graph.add_node(
        _node(
            dec_id,
            NodeType.CERTIFICATION_DECISION,
            ref_id=result.run.certification_id,
            status=result.state.value,
            metadata={"blocked": "true" if result.blocked else "false"},
        )
    )
    graph.add_edge(relate(dec_id, cand_id, RelationType.EVIDENCE_FOR))
    for risk in result.risks:
        rid = f"mrm:{result.candidate.candidate_id}:{risk.category.value}"
        graph.add_node(
            _node(
                rid,
                NodeType.MODEL_RISK_ASSESSMENT,
                ref_id=risk.category.value,
                status=risk.severity.value,
            )
        )
        graph.add_edge(relate(rid, cand_id, RelationType.DERIVED_FROM))
    for waiver in result.waivers:
        wid = f"waiver:{waiver.waiver_id}"
        graph.add_node(
            _node(
                wid,
                NodeType.WAIVER,
                ref_id=waiver.waiver_id,
                metadata={"authority": waiver.authority, "scope": waiver.scope},
            )
        )
        graph.add_edge(relate(wid, cand_id, RelationType.SUPPORTS))
    if result.reproduction is not None:
        rep_id = f"repro:{result.run.certification_id}"
        graph.add_node(
            _node(
                rep_id,
                NodeType.REPRODUCTION_RESULT,
                ref_id=result.run.certification_id,
                status="matched" if result.reproduction.matched else "break",
            )
        )
        graph.add_edge(relate(rep_id, val_id, RelationType.REPLICATED_BY))
        if not result.reproduction.matched:
            dead = f"dead-end:repro-{result.run.certification_id}"
            graph.add_node(
                _node(dead, NodeType.DEAD_END, ref_id=result.run.certification_id, status="repro")
            )
            graph.add_edge(relate(rep_id, dead, RelationType.FALSIFIED_BY, basis="reproduction"))


def persist_certification(result: object, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_certification(graph, result)
    save_graph(graph, path)


def ingest_shadow(graph: KnowledgeGraph, result: object) -> None:
    from quantlab.shadow.models import ShadowResult

    if not isinstance(result, ShadowResult):
        raise KnowledgeError("shadow ingest requires ShadowResult")
    cycle_id = f"shadow-cycle:{result.cycle.cycle_id}"
    graph.add_node(
        _node(
            cycle_id,
            NodeType.SHADOW_CYCLE,
            ref_id=result.cycle.cycle_id,
            status=result.cycle.status.value,
            metadata={"mode": result.cycle.mode.value, "hash": result.cycle.data_snapshot_hash},
        )
    )
    dec_id = f"shadow-decision:{result.cycle.cycle_id}"
    graph.add_node(
        _node(
            dec_id,
            NodeType.SHADOW_DECISION,
            ref_id=result.cycle.cycle_id,
            status=result.cycle.status.value,
        )
    )
    graph.add_edge(relate(dec_id, cycle_id, RelationType.DERIVED_FROM))
    for order in result.orders:
        oid = f"shadow-order:{order.shadow_order_id}"
        graph.add_node(
            _node(
                oid,
                NodeType.SHADOW_ORDER,
                ref_id=order.shadow_order_id,
                status=order.status.value,
            )
        )
        graph.add_edge(relate(oid, cycle_id, RelationType.DERIVED_FROM))
    for fill in result.fills:
        fid = f"shadow-fill:{fill.shadow_fill_id}"
        graph.add_node(
            _node(fid, NodeType.SHADOW_FILL, ref_id=fill.shadow_fill_id, status="simulated")
        )
        graph.add_edge(relate(fid, cycle_id, RelationType.DERIVED_FROM))
    pos_id = f"shadow-position:{result.portfolio.account_id}"
    graph.add_node(
        _node(
            pos_id,
            NodeType.SHADOW_POSITION,
            ref_id=result.portfolio.account_id,
            status=result.portfolio.book.value,
        )
    )
    graph.add_edge(relate(pos_id, cycle_id, RelationType.DERIVED_FROM))
    rec_id = f"shadow-recon:{result.reconciliation.report_id}"
    graph.add_node(
        _node(
            rec_id,
            NodeType.SHADOW_RECONCILIATION,
            ref_id=result.reconciliation.report_id,
            status=result.reconciliation.status,
        )
    )
    graph.add_edge(relate(rec_id, cycle_id, RelationType.TESTED_BY))
    if result.cycle.status.value in {"abstained", "failed", "halted", "rejected"}:
        abs_id = f"shadow-abs:{result.cycle.cycle_id}"
        graph.add_node(
            _node(
                abs_id,
                NodeType.SHADOW_ABSTENTION,
                ref_id=result.cycle.cycle_id,
                status=result.cycle.status.value,
            )
        )
        graph.add_edge(relate(abs_id, cycle_id, RelationType.DERIVED_FROM))
    for incident in result.incidents:
        iid = f"shadow-incident:{incident.incident_id}"
        graph.add_node(
            _node(
                iid,
                NodeType.SHADOW_INCIDENT,
                ref_id=incident.incident_id,
                status=incident.state,
            )
        )
        graph.add_edge(relate(iid, cycle_id, RelationType.DERIVED_FROM))


def persist_shadow(result: object, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_shadow(graph, result)
    save_graph(graph, path)


def ingest_safety(graph: KnowledgeGraph, result: object) -> None:
    from quantlab.safety.models import SafetyResult

    if not isinstance(result, SafetyResult):
        raise KnowledgeError("safety ingest requires SafetyResult")
    eval_id = f"safety:{result.evaluation_id}"
    graph.add_node(
        _node(
            eval_id,
            NodeType.SAFETY_EVALUATION,
            ref_id=result.evaluation_id,
            status=result.state.value,
            metadata={"hash": result.result_hash, "blocked": str(result.blocked)},
        )
    )
    if result.authorization is not None:
        auth_id = f"auth:{result.authorization.authorization_id}"
        graph.add_node(
            _node(
                auth_id,
                NodeType.EXECUTION_AUTHORIZATION,
                ref_id=result.authorization.authorization_id,
                status="non_live",
            )
        )
        graph.add_edge(relate(auth_id, eval_id, RelationType.DERIVED_FROM))
    for incident in result.incidents:
        iid = f"safety-incident:{incident.incident_id}"
        graph.add_node(
            _node(iid, NodeType.SAFETY_INCIDENT, ref_id=incident.incident_id, status=incident.kind)
        )
        graph.add_edge(relate(iid, eval_id, RelationType.DERIVED_FROM))
    kill_id = f"kill:{result.evaluation_id}"
    graph.add_node(
        _node(kill_id, NodeType.KILL_EVENT, ref_id=result.evaluation_id, status="recorded")
    )
    graph.add_edge(relate(kill_id, eval_id, RelationType.DERIVED_FROM))


def persist_safety(result: object, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_safety(graph, result)
    save_graph(graph, path)


def ingest_ops(graph: KnowledgeGraph, result: object) -> None:
    from quantlab.ops.models import OpsResult

    if not isinstance(result, OpsResult):
        raise KnowledgeError("ops ingest requires OpsResult")
    run_id = f"ops:{result.run_id}"
    graph.add_node(
        _node(
            run_id,
            NodeType.OPS_RUN,
            ref_id=result.run_id,
            status=result.state.value,
            metadata={"health": result.health.value, "hash": result.result_hash},
        )
    )
    rel_id = f"ops-release:{result.run_id}"
    graph.add_node(
        _node(rel_id, NodeType.OPS_RELEASE, ref_id=result.run_id, status=result.environment.value)
    )
    graph.add_edge(relate(rel_id, run_id, RelationType.DERIVED_FROM))
    bak_id = f"ops-backup:{result.run_id}"
    graph.add_node(_node(bak_id, NodeType.OPS_BACKUP, ref_id=result.run_id, status="recorded"))
    graph.add_edge(relate(bak_id, run_id, RelationType.DERIVED_FROM))
    for incident in result.incidents:
        iid = f"ops-incident:{incident.incident_id}"
        graph.add_node(
            _node(iid, NodeType.OPS_INCIDENT, ref_id=incident.incident_id, status=incident.kind)
        )
        graph.add_edge(relate(iid, run_id, RelationType.DERIVED_FROM))


def persist_ops(result: object, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_ops(graph, result)
    save_graph(graph, path)


def ingest_release(graph: KnowledgeGraph, result: object) -> None:
    from quantlab.release.models import CertificationResult

    if not isinstance(result, CertificationResult):
        raise KnowledgeError("release ingest requires CertificationResult")
    cert_id = f"live-cert:{result.evaluation_id}"
    graph.add_node(
        _node(
            cert_id,
            NodeType.LIVE_CERTIFICATION,
            ref_id=result.evaluation_id,
            status=result.state.value,
            metadata={"hash": result.result_hash, "blocked": str(result.blocked)},
        )
    )
    if result.manifest is not None:
        man_id = f"release-manifest:{result.manifest.release_id}"
        graph.add_node(
            _node(
                man_id,
                NodeType.RELEASE_MANIFEST,
                ref_id=result.manifest.release_id,
                status="not_live",
                metadata={"hash": result.manifest.manifest_hash},
            )
        )
        graph.add_edge(relate(man_id, cert_id, RelationType.DERIVED_FROM))
        promo_id = f"promotion:{result.evaluation_id}"
        graph.add_node(
            _node(
                promo_id,
                NodeType.PROMOTION_EVENT,
                ref_id=result.evaluation_id,
                status="eligible",
            )
        )
        graph.add_edge(relate(promo_id, cert_id, RelationType.DERIVED_FROM))
    val_id = f"independent-validation:{result.evaluation_id}"
    graph.add_node(
        _node(
            val_id,
            NodeType.INDEPENDENT_VALIDATION,
            ref_id=result.evaluation_id,
            status="recorded",
        )
    )
    graph.add_edge(relate(val_id, cert_id, RelationType.DERIVED_FROM))
    for item in result.criteria:
        if item.blocks:
            find_id = f"cert-finding:{result.evaluation_id}:{item.criterion_id}"
            graph.add_node(
                _node(
                    find_id,
                    NodeType.CERTIFICATION_FINDING,
                    ref_id=item.criterion_id,
                    status=item.verdict.value,
                )
            )
            graph.add_edge(relate(find_id, cert_id, RelationType.DERIVED_FROM))


def persist_release(result: object, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_release(graph, result)
    save_graph(graph, path)


def ingest_broker_gateway(graph: KnowledgeGraph, result: object) -> None:
    from quantlab.broker_gateway.models import GatewaySnapshotBundle

    if not isinstance(result, GatewaySnapshotBundle):
        raise KnowledgeError("broker gateway ingest requires GatewaySnapshotBundle")
    conn_id = f"broker-conn:{result.connection_id}"
    graph.add_node(
        _node(
            conn_id,
            NodeType.BROKER_CONNECTION,
            ref_id=result.connection_id,
            status="read_only",
            metadata={"hash": result.payload_hash, "adapter": result.adapter_id},
        )
    )
    acct_id = f"account-snap:{result.account.snapshot_id}"
    graph.add_node(
        _node(
            acct_id,
            NodeType.ACCOUNT_SNAPSHOT,
            ref_id=result.account.snapshot_id,
            status="hashed",
            metadata={"hash": result.account.payload_hash},
        )
    )
    graph.add_edge(relate(acct_id, conn_id, RelationType.DERIVED_FROM))
    for position in result.positions:
        pid = f"broker-pos:{position.snapshot_id}"
        graph.add_node(
            _node(pid, NodeType.BROKER_POSITION, ref_id=position.snapshot_id, status="read_only")
        )
        graph.add_edge(relate(pid, conn_id, RelationType.DERIVED_FROM))
    for order in result.orders:
        oid = f"broker-ord:{order.broker_order_id}"
        graph.add_node(
            _node(oid, NodeType.BROKER_ORDER, ref_id=order.broker_order_id, status=order.status)
        )
        graph.add_edge(relate(oid, conn_id, RelationType.DERIVED_FROM))
    for fill in result.fills:
        fid = f"broker-fill:{fill.broker_fill_id}"
        graph.add_node(
            _node(fid, NodeType.BROKER_FILL, ref_id=fill.broker_fill_id, status="read_only")
        )
        graph.add_edge(relate(fid, conn_id, RelationType.DERIVED_FROM))
    rec_id = f"broker-recon:{result.bundle_id}"
    graph.add_node(
        _node(rec_id, NodeType.RECONCILIATION, ref_id=result.bundle_id, status="recorded")
    )
    graph.add_edge(relate(rec_id, conn_id, RelationType.DERIVED_FROM))


def persist_broker_gateway(result: object, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_broker_gateway(graph, result)
    save_graph(graph, path)


def ingest_realtime_data(graph: KnowledgeGraph, result: object) -> None:
    from quantlab.realtime_data.models import RealTimeSnapshot

    if not isinstance(result, RealTimeSnapshot):
        raise KnowledgeError("realtime data ingest requires RealTimeSnapshot")
    snap_id = f"rt-snap:{result.snapshot_id}"
    graph.add_node(
        _node(
            snap_id,
            NodeType.REALTIME_SNAPSHOT,
            ref_id=result.snapshot_id,
            status=result.quality.value,
            metadata={"hash": result.snapshot_hash},
        )
    )
    for row in result.observations:
        oid = f"rt-obs:{row.observation_id}"
        graph.add_node(
            _node(
                oid,
                NodeType.MARKET_OBSERVATION,
                ref_id=row.observation_id,
                status=row.quality.value,
            )
        )
        graph.add_edge(relate(oid, snap_id, RelationType.DERIVED_FROM))


def persist_realtime_data(result: object, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_realtime_data(graph, result)
    save_graph(graph, path)


def ingest_realtime_decision(graph: KnowledgeGraph, result: object) -> None:
    from quantlab.realtime_decision.models import RealTimeDecision

    if not isinstance(result, RealTimeDecision):
        raise KnowledgeError("realtime decision ingest requires RealTimeDecision")
    rel_id = f"strategy-rel:{result.release_id}"
    graph.add_node(
        _node(
            rel_id,
            NodeType.STRATEGY_RELEASE,
            ref_id=result.release_id,
            metadata={"hash": result.release_hash},
        )
    )
    dec_id = f"rt-dec:{result.decision_id}"
    graph.add_node(
        _node(
            dec_id,
            NodeType.REALTIME_DECISION,
            ref_id=result.decision_id,
            status=result.state,
            metadata={"hash": result.decision_hash},
        )
    )
    graph.add_edge(relate(dec_id, rel_id, RelationType.DERIVED_FROM))
    snap_id = f"rt-snap:{result.snapshot_id}"
    graph.add_node(_node(snap_id, NodeType.REALTIME_SNAPSHOT, ref_id=result.snapshot_id))
    graph.add_edge(relate(dec_id, snap_id, RelationType.DERIVED_FROM))
    if result.target is not None:
        tp_id = f"target:{result.target.portfolio_id}"
        graph.add_node(
            _node(
                tp_id,
                NodeType.TARGET_PORTFOLIO,
                ref_id=result.target.portfolio_id,
                status="research_only",
            )
        )
        graph.add_edge(relate(tp_id, dec_id, RelationType.DERIVED_FROM))


def persist_realtime_decision(result: object, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_realtime_decision(graph, result)
    save_graph(graph, path)


def ingest_digital_twin(graph: KnowledgeGraph, result: object) -> None:
    from quantlab.digital_twin.models import TwinRun

    if not isinstance(result, TwinRun):
        raise KnowledgeError("digital twin ingest requires TwinRun")
    run_id = f"twin:{result.run_id}"
    graph.add_node(
        _node(
            run_id,
            NodeType.TWIN_RUN,
            ref_id=result.run_id,
            status=result.state,
            metadata={"hash": result.state_hash, "mode": result.mode.value},
        )
    )
    for event in result.events:
        eid = f"twin-evt:{event.event_id}"
        graph.add_node(
            _node(eid, NodeType.TWIN_EVENT, ref_id=event.event_id, status=event.event_type)
        )
        graph.add_edge(relate(eid, run_id, RelationType.DERIVED_FROM))
    for ck in result.checkpoints:
        cid = f"twin-ck:{ck.checkpoint_id}"
        graph.add_node(
            _node(cid, NodeType.TWIN_CHECKPOINT, ref_id=ck.checkpoint_id, status=ck.kind)
        )
        graph.add_edge(relate(cid, run_id, RelationType.DERIVED_FROM))
    if result.counterfactual:
        cf_id = f"twin-cf:{result.run_id}"
        graph.add_node(
            _node(cf_id, NodeType.COUNTERFACTUAL, ref_id=result.run_id, status="not_observed")
        )
        graph.add_edge(relate(cf_id, run_id, RelationType.DERIVED_FROM))
    rec_id = f"twin-recon:{result.run_id}"
    graph.add_node(_node(rec_id, NodeType.RECONCILIATION, ref_id=result.run_id, status="simulated"))
    graph.add_edge(relate(rec_id, run_id, RelationType.DERIVED_FROM))


def persist_digital_twin(result: object, ledger_path: Path) -> None:
    path = Path(ledger_path).with_name("knowledge.json")
    graph = load_graph(path) if path.exists() else KnowledgeGraph(graph_id="kg-ledger")
    ingest_digital_twin(graph, result)
    save_graph(graph, path)
