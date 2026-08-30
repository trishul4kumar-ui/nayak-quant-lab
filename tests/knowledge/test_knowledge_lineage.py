from __future__ import annotations

import pytest

from quantlab.knowledge.entities import KnowledgeNode, NodeType, RelationType
from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.lineage import assert_parents_present, find_lineage
from quantlab.knowledge.relationships import relate

pytestmark = pytest.mark.knowledge


def test_lineage_walk_and_break() -> None:
    graph = KnowledgeGraph()
    parent = KnowledgeNode(node_id="hypothesis:H1", node_type=NodeType.HYPOTHESIS).compute_hashes()
    child = KnowledgeNode(node_id="hypothesis:H2", node_type=NodeType.HYPOTHESIS).compute_hashes()
    graph.add_node(parent)
    graph.add_node(child)
    graph.add_edge(relate("hypothesis:H2", "hypothesis:H1", RelationType.DERIVED_FROM))
    path = find_lineage(graph, "hypothesis:H2")
    assert "hypothesis:H1" in path.node_ids
    with pytest.raises(KnowledgeError, match="lineage_break"):
        find_lineage(graph, "hypothesis:missing")


def test_missing_parent_is_lineage_break() -> None:
    graph = KnowledgeGraph()
    child = KnowledgeNode(node_id="expression:c", node_type=NodeType.EXPRESSION).compute_hashes()
    graph.add_node(child)
    with pytest.raises(KnowledgeError, match="lineage_break"):
        assert_parents_present(graph, child, ["expression:missing-parent"])
