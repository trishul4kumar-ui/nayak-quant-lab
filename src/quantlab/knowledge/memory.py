"""Seeded research memory. Failed work is retained."""

from __future__ import annotations

from pathlib import Path

from quantlab.core.config import get_settings
from quantlab.domain.research import CheckResult
from quantlab.knowledge.entities import (
    AlphaFamily,
    ClaimStatus,
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
from quantlab.knowledge.evidence import add_evidence
from quantlab.knowledge.genealogy import register_hypothesis
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.relationships import relate
from quantlab.knowledge.serialization import load_graph, save_graph
from quantlab.knowledge.snapshots import freeze_snapshot
from quantlab.knowledge.status import add_claim

_PROCESS: KnowledgeGraph | None = None


def seed_graph() -> KnowledgeGraph:
    graph = KnowledgeGraph(graph_id="kg-seed")
    hypo = HypothesisRecord(
        hypothesis_id="H-MOM-001",
        title="Cross-sectional trailing return ranks next-bar returns",
        statement="Higher trailing return predicts higher next-bar cross-sectional return.",
        formal_expression="rank(momentum_20)",
        expected_direction="positive",
        economic_rationale="Under-reaction / continuation on a short horizon.",
        source_type="human",
        pre_registration_id="EXP-MOM-001",
        status=HypothesisStatus.PRE_REGISTERED,
    )
    register_hypothesis(graph, hypo)
    graph.add_node(
        KnowledgeNode(
            node_id="hypothesis:H-MOM-001",
            node_type=NodeType.HYPOTHESIS,
            ref_id="H-MOM-001",
            status=hypo.status.value,
            source="seed",
            metadata={"title": hypo.title},
        ).compute_hashes()
    )
    for feat in ("momentum_5", "momentum_10", "momentum_20", "rolling_std_20"):
        graph.add_node(
            KnowledgeNode(
                node_id=f"feature:{feat}",
                node_type=NodeType.FEATURE,
                ref_id=feat,
                source="seed",
            ).compute_hashes()
        )
    expr_id = "expression:rank-momentum-20"
    graph.add_node(
        KnowledgeNode(
            node_id=expr_id,
            node_type=NodeType.EXPRESSION,
            ref_id="rank(momentum_20)",
            source="seed",
            metadata={"text": "rank(momentum_20)"},
        ).compute_hashes()
    )
    graph.add_edge(relate(expr_id, "feature:momentum_20", RelationType.USES_FEATURE))
    graph.add_edge(relate(expr_id, "hypothesis:H-MOM-001", RelationType.SUPPORTS))
    graph.add_node(
        KnowledgeNode(
            node_id="experiment:EXP-MOM-001",
            node_type=NodeType.EXPERIMENT,
            ref_id="EXP-MOM-001",
            source="seed",
        ).compute_hashes()
    )
    graph.add_edge(relate("experiment:EXP-MOM-001", "hypothesis:H-MOM-001", RelationType.TESTED_BY))
    graph.add_node(
        KnowledgeNode(
            node_id="discovery:GP-MOM-VOL-001",
            node_type=NodeType.DISCOVERY_RUN,
            ref_id="GP-MOM-VOL-001",
            source="seed",
        ).compute_hashes()
    )
    graph.add_edge(
        relate("discovery:GP-MOM-VOL-001", "hypothesis:H-MOM-001", RelationType.PRODUCED_BY)
    )
    graph.add_node(
        KnowledgeNode(
            node_id="family:MOMENTUM",
            node_type=NodeType.ALPHA_FAMILY,
            ref_id="MOMENTUM",
            source="seed",
        ).compute_hashes()
    )
    members = ["feature:momentum_5", "feature:momentum_10", "feature:momentum_20", expr_id]
    for member in members:
        graph.add_edge(relate(member, "family:MOMENTUM", RelationType.MEMBER_OF))
    graph.families.append(
        AlphaFamily(family_id="MOMENTUM", title="Momentum family", member_ids=members)
    )
    graph.add_node(
        KnowledgeNode(
            node_id="family:GP-MOM-VOL-001",
            node_type=NodeType.ALPHA_FAMILY,
            ref_id="GP-MOM-VOL-001",
            source="seed",
        ).compute_hashes()
    )
    graph.families.append(
        AlphaFamily(
            family_id="GP-MOM-VOL-001", title="GP momentum/vol seed family", member_ids=members
        )
    )
    dead = KnowledgeNode(
        node_id="dead-end:DEAD_END-042",
        node_type=NodeType.DEAD_END,
        ref_id="DEAD_END-042",
        status="falsified",
        source="seed",
        metadata={
            "hypothesis": "volatility-adjusted momentum",
            "failure": "OOS effect disappeared",
            "execution": "net edge negative",
            "conclusion": "not robust",
        },
    ).compute_hashes()
    graph.add_node(dead)
    graph.add_edge(relate(expr_id, dead.node_id, RelationType.FALSIFIED_BY, basis="seed_dead_end"))
    ev = EvidenceRecord(
        evidence_id="EVIDENCE-017",
        experiment_id="EXP-MOM-001",
        hypothesis_id="H-MOM-001",
        dataset_id="synthetic",
        snapshot_checksum="seed",
        result_type=EvidenceType.OOS_EVIDENCE,
        metric="ic",
        metric_value=None,
        integrity_status=CheckResult.WARN,
        gate_status="warn",
        data_kind="synthetic",
        limitations=["synthetic data", "no official holidays", "no calibrated ADV"],
    )
    add_evidence(graph, ev)
    graph.add_node(
        KnowledgeNode(
            node_id="evidence:EVIDENCE-017",
            node_type=NodeType.EVIDENCE,
            ref_id="EVIDENCE-017",
            status="warn",
            source="seed",
        ).compute_hashes()
    )
    graph.add_edge(
        relate("evidence:EVIDENCE-017", "hypothesis:H-MOM-001", RelationType.EVIDENCE_FOR)
    )
    add_claim(
        graph,
        ResearchClaim(
            claim_id="CLAIM-MOM-001",
            hypothesis_id="H-MOM-001",
            statement=(
                "20-day momentum showed a recorded OOS IC under the tested research protocol."
            ),
            support_evidence_ids=["EVIDENCE-017"],
            dataset_id="synthetic",
            status=ClaimStatus.PRELIMINARY,
            limitations=ev.limitations,
            knowledge_as_of="seed",
        ),
    )
    graph.accounting.append(
        SearchAccounting(
            family_id="MOM-FAMILY-001",
            search_space_id="MOM-FAMILY-001",
            candidate_count=4,
            tested_count=4,
            selection_policy="pre_registered",
        )
    )
    freeze_snapshot(graph, "KS-SEED-001")
    return graph


def default_path() -> Path:
    return Path(get_settings().experiment_ledger_path).with_name("knowledge.json")


def default_store(*, reload: bool = False) -> KnowledgeGraph:
    global _PROCESS
    if _PROCESS is not None and not reload:
        return _PROCESS
    path = default_path()
    _PROCESS = load_graph(path) if path.exists() else seed_graph()
    return _PROCESS


def persist(graph: KnowledgeGraph, path: Path | None = None) -> None:
    save_graph(graph, path or default_path())
