from __future__ import annotations

import pytest

from quantlab.knowledge.entities import (
    HypothesisRecord,
    HypothesisStatus,
    KnowledgeNode,
    NodeType,
    RelationType,
)
from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.genealogy import attach_parent, descendants, register_hypothesis
from quantlab.knowledge.graph import KnowledgeGraph

pytestmark = pytest.mark.knowledge


def test_mutation_genealogy_requires_parent() -> None:
    graph = KnowledgeGraph()
    parent = HypothesisRecord(
        hypothesis_id="H-PARENT",
        title="parent",
        statement="parent statement",
        status=HypothesisStatus.PROPOSED,
    )
    child = HypothesisRecord(
        hypothesis_id="H-CHILD",
        title="child",
        statement="child statement",
        parent_hypothesis_id="H-PARENT",
        status=HypothesisStatus.PROPOSED,
    )
    register_hypothesis(graph, parent)
    register_hypothesis(graph, child)
    graph.add_node(
        KnowledgeNode(
            node_id="hypothesis:H-CHILD", node_type=NodeType.HYPOTHESIS, ref_id="H-CHILD"
        ).compute_hashes()
    )
    with pytest.raises(KnowledgeError, match="lineage_break"):
        attach_parent(graph, "hypothesis:H-CHILD", "hypothesis:H-PARENT", RelationType.MUTATED_FROM)
    graph.add_node(
        KnowledgeNode(
            node_id="hypothesis:H-PARENT", node_type=NodeType.HYPOTHESIS, ref_id="H-PARENT"
        ).compute_hashes()
    )
    attach_parent(graph, "hypothesis:H-CHILD", "hypothesis:H-PARENT", RelationType.MUTATED_FROM)
    assert "hypothesis:H-PARENT" in descendants(graph, "H-CHILD")
    assert any(edge.relationship_type is RelationType.MUTATED_FROM for edge in graph.edges)
