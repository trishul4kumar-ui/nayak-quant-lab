from __future__ import annotations

import pytest

from quantlab.domain.research import CheckResult
from quantlab.knowledge.entities import (
    ClaimStatus,
    EvidenceRecord,
    KnowledgeNode,
    NodeType,
    RelationType,
    ResearchClaim,
)
from quantlab.knowledge.evidence import add_evidence
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.status import add_claim, detect_contradictions

pytestmark = pytest.mark.knowledge


def test_contradictory_claims_are_both_preserved() -> None:
    graph = KnowledgeGraph()
    graph.add_node(
        KnowledgeNode(
            node_id="experiment:E1", node_type=NodeType.EXPERIMENT, ref_id="E1"
        ).compute_hashes()
    )
    ev_a = EvidenceRecord(
        evidence_id="EV-A",
        experiment_id="E1",
        hypothesis_id="H1",
        data_kind="synthetic",
        integrity_status=CheckResult.WARN,
    )
    ev_b = EvidenceRecord(
        evidence_id="EV-B",
        experiment_id="E1",
        hypothesis_id="H1",
        data_kind="synthetic",
        integrity_status=CheckResult.WARN,
    )
    add_evidence(graph, ev_a)
    add_evidence(graph, ev_b)
    add_claim(
        graph,
        ResearchClaim(
            claim_id="C-POS",
            hypothesis_id="H1",
            statement="momentum is positive",
            support_evidence_ids=["EV-A"],
            status=ClaimStatus.SUPPORTED,
        ),
    )
    add_claim(
        graph,
        ResearchClaim(
            claim_id="C-NEG",
            hypothesis_id="H1",
            statement="momentum is negative",
            support_evidence_ids=["EV-B"],
            status=ClaimStatus.FALSIFIED,
        ),
    )
    pairs = detect_contradictions(graph)
    assert len(pairs) == 1
    ids = {item.claim_id for item in graph.claims}
    assert ids == {"C-POS", "C-NEG"}
    assert any(edge.relationship_type is RelationType.CONTRADICTS for edge in graph.edges)
