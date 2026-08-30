from __future__ import annotations

import pytest

from quantlab import __version__
from quantlab.core.config import LiveSafetyGates
from quantlab.knowledge.memory import seed_graph
from quantlab.knowledge.query import find_hypothesis
from quantlab.knowledge.report import knowledge_report

pytestmark = pytest.mark.knowledge


def test_knowledge_e2e_seed_memory() -> None:
    graph = seed_graph()
    assert __version__ == "3.1.0"
    assert LiveSafetyGates().live_trading is False
    hypo = find_hypothesis(graph, "H-MOM-001")
    assert hypo is not None
    report = knowledge_report(graph, "H-MOM-001")
    assert report["STATUS"] == "preliminary"
    assert report["data_kind"] == "synthetic"
    assert any(item.node_type.value == "dead_end" for item in graph.nodes)
    assert graph.graph_hash() == seed_graph().graph_hash()
