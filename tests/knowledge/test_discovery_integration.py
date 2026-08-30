from __future__ import annotations

import pytest
from tests.knowledge.factories import discovery_report

from quantlab.knowledge.entities import NodeType
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.ingest import ingest_discovery_report
from quantlab.knowledge.query import find_dead_ends

pytestmark = pytest.mark.knowledge


def test_discovery_candidates_become_knowledge_including_failures() -> None:
    graph = KnowledgeGraph()
    ingest_discovery_report(graph, discovery_report())
    types = {item.node_type for item in graph.nodes}
    assert NodeType.DISCOVERY_RUN in types
    assert NodeType.EXPRESSION in types
    assert NodeType.DEAD_END in types
    assert NodeType.FALSIFICATION in types
    assert find_dead_ends(graph)
    assert graph.accounting[0].tested_count == 2
    assert graph.accounting[0].falsified_count == 1
