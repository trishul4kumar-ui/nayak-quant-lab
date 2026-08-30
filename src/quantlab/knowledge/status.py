"""Research claims. Claims must never be stronger than their evidence."""

from __future__ import annotations

from datetime import UTC, datetime

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
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.relationships import relate

_STRENGTH = {
    ClaimStatus.UNSUPPORTED: 0,
    ClaimStatus.PRELIMINARY: 1,
    ClaimStatus.SUPPORTED: 2,
    ClaimStatus.REPLICATED: 3,
    ClaimStatus.VALIDATED: 4,
    ClaimStatus.CONTRADICTED: 1,
    ClaimStatus.FALSIFIED: 1,
}


def add_claim(graph: KnowledgeGraph, claim: ResearchClaim) -> ResearchClaim:
    if not claim.support_evidence_ids and claim.status not in {
        ClaimStatus.UNSUPPORTED,
        ClaimStatus.FALSIFIED,
    }:
        raise KnowledgeError("claim_without_evidence")
    evidence = [item for item in graph.evidence if item.evidence_id in claim.support_evidence_ids]
    if claim.support_evidence_ids and len(evidence) != len(set(claim.support_evidence_ids)):
        raise KnowledgeError("claim_without_evidence")
    _assert_not_stronger(claim, evidence)
    _assert_temporal(claim, evidence)
    for item in graph.claims:
        if item.claim_id == claim.claim_id:
            if item.statement != claim.statement or item.status != claim.status:
                raise KnowledgeError("historical_claim_mutation")
            return item
    graph.claims.append(claim)
    _ensure_claim_node(graph, claim)
    return claim


def supersede_claim(graph: KnowledgeGraph, old: ResearchClaim, new: ResearchClaim) -> ResearchClaim:
    if old.claim_id not in {item.claim_id for item in graph.claims}:
        raise KnowledgeError("cannot supersede a missing claim; old claims must be preserved")
    added = add_claim(graph, new.model_copy(update={"superseded_by": ""}))
    old_id = _ensure_claim_node(graph, old)
    new_id = _ensure_claim_node(graph, added)
    graph.add_edge(relate(new_id, old_id, RelationType.SUPERSEDES, basis="supersede"))
    return added


def drop_claim(graph: KnowledgeGraph, claim_id: str) -> None:
    del graph, claim_id
    raise KnowledgeError("historical_claim_mutation: old claims must be preserved")


def mutate_claim(graph: KnowledgeGraph, claim_id: str) -> None:
    del graph, claim_id
    raise KnowledgeError("historical_claim_mutation")


def _assert_not_stronger(claim: ResearchClaim, evidence: list[EvidenceRecord]) -> None:
    if (
        claim.origin is not ContentOrigin.EMPIRICAL
        and _STRENGTH[claim.status] >= _STRENGTH[ClaimStatus.SUPPORTED]
    ):
        raise KnowledgeError("ai_evidence_confusion: AI text cannot support an empirical claim")
    if any(item.data_kind == "synthetic" for item in evidence) and claim.status in {
        ClaimStatus.VALIDATED,
        ClaimStatus.REPLICATED,
    }:
        raise KnowledgeError("synthetic_evidence_overpromotion")
    if claim.status is ClaimStatus.VALIDATED and not evidence:
        raise KnowledgeError("claim_overstates_evidence")
    if claim.status is ClaimStatus.SUPPORTED and not evidence:
        raise KnowledgeError("claim_without_evidence")


def detect_contradictions(graph: KnowledgeGraph) -> list[tuple[ResearchClaim, ResearchClaim]]:
    pairs: list[tuple[ResearchClaim, ResearchClaim]] = []
    items = graph.claims
    for i, left in enumerate(items):
        for right in items[i + 1 :]:
            if left.hypothesis_id != right.hypothesis_id:
                continue
            opposed = (
                left.status is ClaimStatus.SUPPORTED and right.status is ClaimStatus.FALSIFIED
            ) or (left.status is ClaimStatus.FALSIFIED and right.status is ClaimStatus.SUPPORTED)
            if opposed:
                pairs.append((left, right))
                left_id = _ensure_claim_node(graph, left)
                right_id = _ensure_claim_node(graph, right)
                graph.add_edge(
                    relate(left_id, right_id, RelationType.CONTRADICTS, basis="unresolved")
                )
    return pairs


def _assert_temporal(claim: ResearchClaim, evidence: list[EvidenceRecord]) -> None:
    cutoff = _as_datetime(claim.knowledge_as_of)
    if cutoff is None:
        return
    for item in evidence:
        created = item.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        if created > cutoff:
            raise KnowledgeError(
                "future_claim_context: evidence created after claim knowledge_as_of"
            )
        period = _as_datetime(item.train_period) or _as_datetime(item.test_period)
        if period is not None and period > cutoff:
            raise KnowledgeError("future_knowledge_leak: later data used for an earlier claim")


def _as_datetime(value: str) -> datetime | None:
    if not value or value in {"seed", "synthetic"}:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _ensure_claim_node(graph: KnowledgeGraph, claim: ResearchClaim) -> str:
    node_id = f"claim:{claim.claim_id}"
    if node_id not in graph.node_map():
        graph.add_node(
            KnowledgeNode(
                node_id=node_id,
                node_type=NodeType.RESEARCH_CLAIM,
                ref_id=claim.claim_id,
                status=claim.status.value,
                source="claim",
            ).compute_hashes()
        )
    return node_id
