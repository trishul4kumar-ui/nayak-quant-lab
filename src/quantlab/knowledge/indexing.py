"""In-memory indexes over the knowledge graph."""

from __future__ import annotations

from collections import defaultdict

from quantlab.knowledge.entities import KnowledgeNode, RelationType
from quantlab.knowledge.graph import KnowledgeGraph


class KnowledgeIndex:
    def __init__(self, graph: KnowledgeGraph) -> None:
        self.by_type: dict[str, list[KnowledgeNode]] = defaultdict(list)
        self.by_status: dict[str, list[KnowledgeNode]] = defaultdict(list)
        self.by_ref: dict[str, KnowledgeNode] = {}
        self.by_relation: dict[RelationType, list[str]] = defaultdict(list)
        for node in graph.nodes:
            self.by_type[node.node_type.value].append(node)
            self.by_status[node.status].append(node)
            if node.ref_id:
                self.by_ref[node.ref_id] = node
        for edge in graph.edges:
            self.by_relation[edge.relationship_type].append(edge.edge_id)
