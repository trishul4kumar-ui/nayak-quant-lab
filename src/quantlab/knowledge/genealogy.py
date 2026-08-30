"""Hypothesis genealogy. Prompt 15 ancestry is never dropped when candidates are pruned."""

from __future__ import annotations

from quantlab.knowledge.entities import (
    HypothesisRecord,
    HypothesisStatus,
    NodeType,
    RelationType,
)
from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.relationships import relate


def register_hypothesis(graph: KnowledgeGraph, record: HypothesisRecord) -> HypothesisRecord:
    if record.status is HypothesisStatus.SUPPORTED:
        # Supported ≠ profitable; stored as-is with that reminder in metadata.
        pass
    for item in graph.hypotheses:
        if item.hypothesis_id == record.hypothesis_id:
            if item.statement != record.statement or item.title != record.title:
                raise KnowledgeError("hypothesis identity mutated; bump version instead")
            return item
    graph.hypotheses.append(record)
    return record


def attach_parent(graph: KnowledgeGraph, child_id: str, parent_id: str, rel: RelationType) -> None:
    if parent_id not in graph.node_map():
        raise KnowledgeError(f"lineage_break: parent {parent_id} missing")
    graph.add_edge(relate(child_id, parent_id, rel, basis="genealogy"))


def descendants(graph: KnowledgeGraph, hypothesis_id: str) -> list[str]:
    node_id = f"hypothesis:{hypothesis_id}"
    return [item for item in graph.walk(node_id) if item != node_id]


def family_members(graph: KnowledgeGraph, family_id: str) -> list[str]:
    for family in graph.families:
        if family.family_id == family_id:
            return list(family.member_ids)
    return []


def hypothesis_nodes(graph: KnowledgeGraph) -> list[str]:
    return [item.node_id for item in graph.nodes if item.node_type is NodeType.HYPOTHESIS]
