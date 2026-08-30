"""Typed graph operations. Historical nodes are never deleted."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.backtest.spec import config_hash
from quantlab.knowledge.entities import (
    AlphaFamily,
    EvidenceRecord,
    HypothesisRecord,
    KnowledgeEdge,
    KnowledgeNode,
    KnowledgeSnapshot,
    RelationType,
    ReplicationRecord,
    ResearchClaim,
    SearchAccounting,
)
from quantlab.knowledge.errors import KnowledgeError


class KnowledgeGraph(BaseModel):
    schema_version: str = "1"
    graph_id: str = "kg-default"
    nodes: list[KnowledgeNode] = Field(default_factory=list)
    edges: list[KnowledgeEdge] = Field(default_factory=list)
    hypotheses: list[HypothesisRecord] = Field(default_factory=list)
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    claims: list[ResearchClaim] = Field(default_factory=list)
    replications: list[ReplicationRecord] = Field(default_factory=list)
    families: list[AlphaFamily] = Field(default_factory=list)
    accounting: list[SearchAccounting] = Field(default_factory=list)
    snapshots: list[KnowledgeSnapshot] = Field(default_factory=list)

    def node_map(self) -> dict[str, KnowledgeNode]:
        return {item.node_id: item for item in self.nodes}

    def add_node(self, node: KnowledgeNode) -> KnowledgeNode:
        hashed = node if node.content_hash else node.compute_hashes()
        existing = self.node_map().get(hashed.node_id)
        if existing is not None:
            if existing.content_hash != hashed.content_hash:
                raise KnowledgeError(
                    f"duplicate identity collision for {hashed.node_id}; "
                    "historical nodes are immutable"
                )
            return existing
        self.nodes.append(hashed)
        return hashed

    def add_edge(self, edge: KnowledgeEdge) -> KnowledgeEdge:
        ids = self.node_map()
        if edge.source_id not in ids or edge.target_id not in ids:
            raise KnowledgeError("knowledge_provenance_break: edge references missing nodes")
        for item in self.edges:
            if item.edge_id == edge.edge_id:
                if item.identity_payload() != edge.identity_payload():
                    raise KnowledgeError("edge identity mutated")
                return item
        self.edges.append(edge)
        return edge

    def delete_node(self, node_id: str) -> None:
        raise KnowledgeError(
            f"candidate_history_deleted: refusing to delete {node_id}; "
            "failed research is first-class"
        )

    def mutate_node(self, node_id: str, **_updates: object) -> None:
        raise KnowledgeError(f"historical mutation refused for {node_id}")

    def graph_hash(self) -> str:
        nodes = sorted(
            (item.identity_payload() for item in self.nodes), key=lambda row: str(row["node_id"])
        )
        edges = sorted(
            (item.identity_payload() for item in self.edges),
            key=lambda row: (
                str(row["source_id"]),
                str(row["target_id"]),
                str(row["relationship_type"]),
                str(row["edge_id"]),
            ),
        )
        return config_hash({"schema": self.schema_version, "nodes": nodes, "edges": edges})

    def walk(self, start_id: str, *, reverse: bool = False) -> list[str]:
        adj: dict[str, list[str]] = {}
        for edge in self.edges:
            src, dst = (
                (edge.target_id, edge.source_id) if reverse else (edge.source_id, edge.target_id)
            )
            adj.setdefault(src, []).append(dst)
        seen: list[str] = []
        stack = [start_id]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.append(current)
            stack.extend(reversed(adj.get(current, [])))
        return seen


def edge_id(source: str, target: str, rel: RelationType) -> str:
    return f"{rel.value}:{source}->{target}"
