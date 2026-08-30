from __future__ import annotations

import pytest

from quantlab.knowledge.entities import KnowledgeNode, NodeType
from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.memory import seed_graph

pytestmark = pytest.mark.knowledge


def test_seed_graph_hash_is_deterministic() -> None:
    assert seed_graph().graph_hash() == seed_graph().graph_hash()


def test_duplicate_identity_collision() -> None:
    graph = KnowledgeGraph()
    node = KnowledgeNode(
        node_id="expression:x",
        node_type=NodeType.EXPRESSION,
        ref_id="rank(momentum_20)",
        metadata={"text": "rank(momentum_20)"},
    ).compute_hashes()
    graph.add_node(node)
    mutated = KnowledgeNode(
        node_id="expression:x",
        node_type=NodeType.EXPRESSION,
        ref_id="rank(momentum_5)",
        metadata={"text": "rank(momentum_5)"},
    ).compute_hashes()
    with pytest.raises(KnowledgeError, match="duplicate identity collision"):
        graph.add_node(mutated)
