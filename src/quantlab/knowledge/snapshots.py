"""Immutable knowledge snapshots. Historical reports replay against a frozen graph hash."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab import __version__
from quantlab.knowledge.entities import KnowledgeSnapshot
from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.graph import KnowledgeGraph


def freeze_snapshot(graph: KnowledgeGraph, snapshot_id: str) -> KnowledgeSnapshot:
    digest = graph.graph_hash()
    snap = KnowledgeSnapshot(
        knowledge_snapshot_id=snapshot_id,
        created_at=datetime.now(tz=UTC),
        graph_hash=digest,
        node_count=len(graph.nodes),
        edge_count=len(graph.edges),
        software_version=__version__,
        payload={
            "node_ids": sorted(item.node_id for item in graph.nodes),
            "edge_ids": sorted(item.edge_id for item in graph.edges),
            "hypothesis_ids": sorted(item.hypothesis_id for item in graph.hypotheses),
            "evidence_ids": sorted(item.evidence_id for item in graph.evidence),
            "claim_ids": sorted(item.claim_id for item in graph.claims),
        },
    )
    for item in graph.snapshots:
        if item.knowledge_snapshot_id == snapshot_id:
            if item.graph_hash != digest:
                raise KnowledgeError("snapshot_mutation")
            return item
    graph.snapshots.append(snap)
    return snap


def mutate_snapshot(graph: KnowledgeGraph, snapshot_id: str) -> None:
    del graph, snapshot_id
    raise KnowledgeError("snapshot_mutation: frozen snapshots cannot be rewritten")


def diff_snapshots(left: KnowledgeSnapshot, right: KnowledgeSnapshot) -> dict[str, list[str]]:
    def _ids(snap: KnowledgeSnapshot, key: str) -> set[str]:
        raw = snap.payload.get(key, [])
        if not isinstance(raw, list):
            return set()
        return {str(item) for item in raw}

    return {
        "new_nodes": sorted(_ids(right, "node_ids") - _ids(left, "node_ids")),
        "removed_nodes": sorted(_ids(left, "node_ids") - _ids(right, "node_ids")),
        "new_hypotheses": sorted(_ids(right, "hypothesis_ids") - _ids(left, "hypothesis_ids")),
        "new_evidence": sorted(_ids(right, "evidence_ids") - _ids(left, "evidence_ids")),
        "new_claims": sorted(_ids(right, "claim_ids") - _ids(left, "claim_ids")),
        "hash_changed": [left.graph_hash, right.graph_hash]
        if left.graph_hash != right.graph_hash
        else [],
    }
