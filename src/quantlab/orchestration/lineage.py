"""Queryable research lineage. Deleting a parent is a lineage break."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.orchestration.errors import OrchestrationError


class LineageNode(BaseModel):
    node_id: str
    kind: str
    parent_id: str = ""
    children: list[str] = Field(default_factory=list)
    status: str = ""
    note: str = ""


class ResearchGraph(BaseModel):
    hypothesis_id: str
    family_id: str
    nodes: list[LineageNode] = Field(default_factory=list)

    def ids(self) -> set[str]:
        return {n.node_id for n in self.nodes}

    def parent_of(self, node_id: str) -> str:
        for node in self.nodes:
            if node.node_id == node_id:
                return node.parent_id
        return ""


def build_graph(
    *,
    hypothesis_id: str,
    family_id: str,
    candidate_ids: list[str],
    parent_experiment: str = "",
    extra: list[LineageNode] | None = None,
) -> ResearchGraph:
    nodes = [
        LineageNode(node_id=hypothesis_id, kind="hypothesis", status="registered"),
        LineageNode(
            node_id=family_id,
            kind="family",
            parent_id=hypothesis_id,
            children=list(candidate_ids),
        ),
    ]
    if parent_experiment:
        nodes.append(
            LineageNode(
                node_id=parent_experiment,
                kind="experiment",
                parent_id=family_id,
                children=list(candidate_ids),
            )
        )
    parent = parent_experiment or family_id
    for cid in candidate_ids:
        nodes.append(
            LineageNode(
                node_id=cid,
                kind="candidate",
                parent_id=parent,
            )
        )
    if extra:
        nodes.extend(extra)
    return ResearchGraph(hypothesis_id=hypothesis_id, family_id=family_id, nodes=nodes)


def assert_lineage_intact(graph: ResearchGraph, *, deleted_parent: str = "") -> None:
    if deleted_parent and deleted_parent in {n.parent_id for n in graph.nodes}:
        raise OrchestrationError(f"lineage parent deleted: {deleted_parent}")
    known = graph.ids()
    for node in graph.nodes:
        if (
            node.parent_id
            and node.parent_id not in known
            and node.kind != "hypothesis"
            and node.parent_id not in {graph.hypothesis_id, graph.family_id}
        ):
            raise OrchestrationError(f"lineage break: missing parent {node.parent_id}")
