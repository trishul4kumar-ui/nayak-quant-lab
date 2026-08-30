"""App-layer knowledge services. CLI and desktop call these."""

from __future__ import annotations

from typing import Any

from quantlab.discovery.errors import DiscoveryError
from quantlab.discovery.generator import human_hypothesis, seed_expressions
from quantlab.discovery.grammar import GrammarSpec
from quantlab.knowledge.lineage import find_lineage
from quantlab.knowledge.memory import default_store, persist, seed_graph
from quantlab.knowledge.query import (
    find_alpha_family,
    find_dead_ends,
    find_evidence,
    find_failures,
    find_hypothesis,
    find_replications,
    find_research_claims,
)
from quantlab.knowledge.report import knowledge_report
from quantlab.knowledge.serialization import dump_graph
from quantlab.knowledge.similarity import expression_similarity
from quantlab.knowledge.snapshots import diff_snapshots, freeze_snapshot
from quantlab.knowledge.status import detect_contradictions


def _graph() -> Any:
    return default_store()


def list_payload() -> list[dict[str, Any]]:
    graph = _graph()
    return [
        {
            "node_id": item.node_id,
            "type": item.node_type.value,
            "status": item.status,
            "identity": item.content_hash,
        }
        for item in graph.nodes
    ]


def inspect_payload(item_id: str) -> dict[str, Any]:
    graph = _graph()
    hypo = find_hypothesis(graph, item_id)
    if hypo is not None:
        payload: dict[str, Any] = dict(hypo.model_dump(mode="json"))
        payload["note"] = "A hypothesis in memory is not evidence. SUPPORTED ≠ profitable."
        return payload
    node = graph.node_map().get(item_id) or graph.node_map().get(f"hypothesis:{item_id}")
    if node is None:
        return {"error": f"unknown id {item_id}"}
    return dict(node.model_dump(mode="json"))


def search_payload(query: str) -> list[dict[str, Any]]:
    needle = query.lower()
    return [row for row in list_payload() if needle in json_blob(row)]


def json_blob(row: dict[str, Any]) -> str:
    return " ".join(str(v).lower() for v in row.values())


def graph_payload(item_id: str) -> dict[str, Any]:
    graph = _graph()
    nid = item_id if item_id in graph.node_map() else f"hypothesis:{item_id}"
    edges = [
        edge.model_dump(mode="json")
        for edge in graph.edges
        if edge.source_id == nid or edge.target_id == nid
    ]
    return {
        "node_id": nid,
        "edges": edges,
        "note": "Graph is memory. It does not authorize trading.",
    }


def lineage_payload(item_id: str) -> dict[str, Any]:
    graph = _graph()
    nid = item_id if ":" in item_id else f"hypothesis:{item_id}"
    path = find_lineage(graph, nid)
    return path.model_dump(mode="json")


def evidence_payload(item_id: str) -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in find_evidence(_graph(), item_id)]


def status_payload(item_id: str) -> dict[str, Any]:
    graph = _graph()
    hypo = find_hypothesis(graph, item_id)
    claims = find_research_claims(graph, item_id)
    return {
        "hypothesis_id": item_id,
        "status": hypo.status.value if hypo else "not_tested",
        "claims": [item.status.value for item in claims],
        "evidence": len(find_evidence(graph, item_id)),
        "note": "Prompt 05 remains the only promotion gate.",
    }


def similar_payload(item_id: str) -> dict[str, Any]:
    grammar = GrammarSpec()
    seeds = seed_expressions(grammar)
    try:
        expr = human_hypothesis(item_id, grammar)
    except DiscoveryError:
        expr = seeds[1]
    peer = seeds[0]
    return {
        "left": expr.canonical_text(),
        "right": peer.canonical_text(),
        "class": expression_similarity(expr, peer).value,
        "note": "Syntactic similarity is not statistical independence.",
    }


def family_payload(item_id: str) -> dict[str, Any]:
    return {"family_id": item_id, "members": find_alpha_family(_graph(), item_id)}


def failures_payload() -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in find_failures(_graph())]


def dead_end_payload() -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in find_dead_ends(_graph())]


def replication_payload(item_id: str) -> dict[str, Any]:
    return {"hypothesis_id": item_id, "replications": find_replications(_graph(), item_id)}


def contradiction_payload() -> list[dict[str, Any]]:
    pairs = detect_contradictions(_graph())
    return [
        {"left": left.claim_id, "right": right.claim_id, "hypothesis_id": left.hypothesis_id}
        for left, right in pairs
    ]


def snapshot_payload() -> dict[str, Any]:
    graph = _graph()
    snap = freeze_snapshot(graph, f"KS-{len(graph.snapshots) + 1:03d}")
    persist(graph)
    return snap.model_dump(mode="json")


def diff_payload(snapshot_a: str, snapshot_b: str) -> dict[str, Any]:
    graph = _graph()
    by_id = {item.knowledge_snapshot_id: item for item in graph.snapshots}
    left = by_id.get(snapshot_a)
    right = by_id.get(snapshot_b)
    if left is None or right is None:
        return {"error": "snapshot not found", "known": list(by_id)}
    return diff_snapshots(left, right)


def report_payload(hypothesis_id: str) -> dict[str, Any]:
    return knowledge_report(_graph(), hypothesis_id)


def export_payload() -> dict[str, Any]:
    return {"json": dump_graph(_graph()), "note": "Export is a memory dump, not a live book."}


def catalog_rows() -> list[dict[str, Any]]:
    return list_payload()


def node_table_rows(*, node_type: str = "all") -> list[list[str]]:
    rows: list[list[str]] = []
    for item in _graph().nodes:
        if node_type not in {"", "all"} and item.node_type.value != node_type:
            continue
        rows.append(
            [
                item.node_id,
                item.node_type.value,
                item.status,
                item.content_hash[:16],
            ]
        )
    return rows


def edge_table_rows(*, relationship: str = "all") -> list[list[str]]:
    rows: list[list[str]] = []
    for edge in _graph().edges:
        if relationship not in {"", "all"} and edge.relationship_type.value != relationship:
            continue
        rows.append(
            [
                edge.source_id,
                edge.relationship_type.value,
                edge.target_id,
                edge.confidence_basis,
            ]
        )
    return rows


def last_snapshot_row() -> dict[str, Any] | None:
    snaps = _graph().snapshots
    if not snaps:
        seed_graph()
        snaps = _graph().snapshots
    if not snaps:
        return None
    item = snaps[-1]
    return {
        "id": item.knowledge_snapshot_id,
        "hash": item.graph_hash,
        "nodes": item.node_count,
        "edges": item.edge_count,
        "version": item.software_version,
    }
