"""Relationship constructors. Edges carry provenance when applicable."""

from __future__ import annotations

from quantlab.knowledge.entities import KnowledgeEdge, RelationType
from quantlab.knowledge.graph import edge_id


def relate(
    source_id: str,
    target_id: str,
    rel: RelationType,
    *,
    experiment_id: str = "",
    evidence_id: str = "",
    basis: str = "recorded",
) -> KnowledgeEdge:
    return KnowledgeEdge(
        edge_id=edge_id(source_id, target_id, rel),
        source_id=source_id,
        target_id=target_id,
        relationship_type=rel,
        source_experiment_id=experiment_id,
        evidence_id=evidence_id,
        confidence_basis=basis,
    )
