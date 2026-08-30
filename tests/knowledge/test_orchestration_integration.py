from __future__ import annotations

import pytest
from tests.knowledge.factories import orchestration_report

from quantlab.knowledge.entities import NodeType
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.ingest import ingest_orchestration_report

pytestmark = pytest.mark.knowledge


def test_orchestration_experiment_is_linked() -> None:
    graph = KnowledgeGraph()
    ingest_orchestration_report(graph, orchestration_report())
    types = {item.node_type for item in graph.nodes}
    assert NodeType.EXPERIMENT in types
    assert NodeType.HYPOTHESIS in types
    assert NodeType.DATASET_SNAPSHOT in types
    assert graph.accounting[0].selection_policy == "pre_registered"
    assert graph.accounting[0].tested_count == 1
    assert graph.claims
