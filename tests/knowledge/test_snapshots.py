from __future__ import annotations

import pytest

from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.memory import seed_graph
from quantlab.knowledge.snapshots import diff_snapshots, freeze_snapshot, mutate_snapshot

pytestmark = pytest.mark.knowledge


def test_snapshot_hash_is_deterministic() -> None:
    graph = seed_graph()
    freeze_snapshot(graph, "KS-SEED-001")
    other = seed_graph()
    assert graph.graph_hash() == other.graph_hash()


def test_snapshot_mutation_is_refused() -> None:
    graph = KnowledgeGraph()
    freeze_snapshot(graph, "KS-1")
    with pytest.raises(KnowledgeError, match="snapshot_mutation"):
        mutate_snapshot(graph, "KS-1")


def test_snapshot_diff_lists_new_nodes() -> None:
    graph = KnowledgeGraph()
    a = freeze_snapshot(graph, "A")
    from quantlab.knowledge.entities import KnowledgeNode, NodeType

    graph.add_node(
        KnowledgeNode(node_id="hypothesis:H-X", node_type=NodeType.HYPOTHESIS).compute_hashes()
    )
    b = freeze_snapshot(graph, "B")
    diff = diff_snapshots(a, b)
    assert "hypothesis:H-X" in diff["new_nodes"]
    assert diff["hash_changed"]
