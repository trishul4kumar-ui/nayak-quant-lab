"""Knowledge-level lineage traversal. Distinct from orchestration/discovery lineage graphs."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.knowledge.entities import KnowledgeEdge, KnowledgeNode
from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.graph import KnowledgeGraph


class LineagePath(BaseModel):
    start_id: str
    node_ids: list[str] = Field(default_factory=list)
    edges: list[KnowledgeEdge] = Field(default_factory=list)
    broken: bool = False


def find_lineage(graph: KnowledgeGraph, node_id: str, *, reverse: bool = False) -> LineagePath:
    if node_id not in graph.node_map():
        raise KnowledgeError(f"lineage_break: unknown node {node_id}")
    ids = graph.walk(node_id, reverse=reverse)
    known = graph.node_map()
    broken = any(item not in known for item in ids)
    edges = [edge for edge in graph.edges if edge.source_id in ids and edge.target_id in ids]
    return LineagePath(start_id=node_id, node_ids=ids, edges=edges, broken=broken)


def assert_parents_present(
    graph: KnowledgeGraph, node: KnowledgeNode, parent_ids: list[str]
) -> None:
    known = graph.node_map()
    missing = [
        item for item in parent_ids if item and item not in known and not item.startswith("seed:")
    ]
    if missing:
        raise KnowledgeError(f"lineage_break: missing parents {missing} for {node.node_id}")
