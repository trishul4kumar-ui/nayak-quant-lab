from __future__ import annotations

import pytest

from quantlab.domain.research import CheckResult
from quantlab.knowledge.entities import (
    ClaimStatus,
    ContentOrigin,
    EvidenceRecord,
    KnowledgeNode,
    NodeType,
    RelationType,
    ResearchClaim,
)
from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.evidence import add_evidence
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.status import add_claim, drop_claim, supersede_claim

pytestmark = pytest.mark.knowledge


def _graph_with_evidence() -> tuple[KnowledgeGraph, EvidenceRecord]:
    graph = KnowledgeGraph()
    graph.add_node(
        KnowledgeNode(
            node_id="experiment:E1", node_type=NodeType.EXPERIMENT, ref_id="E1"
        ).compute_hashes()
    )
    ev = EvidenceRecord(
        evidence_id="EV-1",
        experiment_id="E1",
        hypothesis_id="H1",
        data_kind="synthetic",
        integrity_status=CheckResult.WARN,
    )
    add_evidence(graph, ev)
    return graph, ev


def test_unsupported_claim_without_evidence_fails_when_strong() -> None:
    graph, _ev = _graph_with_evidence()
    with pytest.raises(KnowledgeError, match="claim_without_evidence"):
        add_claim(
            graph,
            ResearchClaim(
                claim_id="C-STRONG",
                hypothesis_id="H1",
                statement="alpha is real",
                status=ClaimStatus.SUPPORTED,
            ),
        )
    add_claim(
        graph,
        ResearchClaim(
            claim_id="C-NONE",
            hypothesis_id="H1",
            statement="not yet tested",
            status=ClaimStatus.UNSUPPORTED,
        ),
    )


def test_synthetic_cannot_be_validated() -> None:
    graph, ev = _graph_with_evidence()
    with pytest.raises(KnowledgeError, match="synthetic_evidence_overpromotion"):
        add_claim(
            graph,
            ResearchClaim(
                claim_id="C-VAL",
                hypothesis_id="H1",
                statement="validated on synthetic",
                support_evidence_ids=[ev.evidence_id],
                status=ClaimStatus.VALIDATED,
            ),
        )


def test_ai_claim_cannot_be_empirical_support() -> None:
    graph, ev = _graph_with_evidence()
    with pytest.raises(KnowledgeError, match="ai_evidence_confusion"):
        add_claim(
            graph,
            ResearchClaim(
                claim_id="C-AI",
                hypothesis_id="H1",
                statement="the model said so",
                support_evidence_ids=[ev.evidence_id],
                status=ClaimStatus.SUPPORTED,
                origin=ContentOrigin.AI_GENERATED_RESEARCH_SUGGESTION,
            ),
        )


def test_supersede_preserves_old_claim() -> None:
    graph, ev = _graph_with_evidence()
    old = add_claim(
        graph,
        ResearchClaim(
            claim_id="C-OLD",
            hypothesis_id="H1",
            statement="preliminary IC",
            support_evidence_ids=[ev.evidence_id],
            status=ClaimStatus.PRELIMINARY,
        ),
    )
    new = ResearchClaim(
        claim_id="C-NEW",
        hypothesis_id="H1",
        statement="updated preliminary IC",
        support_evidence_ids=[ev.evidence_id],
        status=ClaimStatus.PRELIMINARY,
    )
    supersede_claim(graph, old, new)
    ids = {item.claim_id for item in graph.claims}
    assert "C-OLD" in ids and "C-NEW" in ids
    assert old.statement == "preliminary IC"
    assert any(edge.relationship_type is RelationType.SUPERSEDES for edge in graph.edges)
    with pytest.raises(KnowledgeError, match="historical_claim_mutation"):
        drop_claim(graph, "C-OLD")
