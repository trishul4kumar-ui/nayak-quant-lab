from __future__ import annotations

import pytest
from tests.knowledge.factories import discovery_report, orchestration_report

from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.ingest import ingest_discovery_report, ingest_orchestration_report

pytestmark = pytest.mark.knowledge


def test_hiding_discarded_candidates_fails() -> None:
    graph = KnowledgeGraph()
    with pytest.raises(KnowledgeError, match="search_degree_of_freedom_loss"):
        ingest_discovery_report(graph, discovery_report(hidden=True))


def test_hidden_orchestration_candidate_fails() -> None:
    graph = KnowledgeGraph()
    with pytest.raises(KnowledgeError, match="search_degree_of_freedom_loss"):
        ingest_orchestration_report(graph, orchestration_report(hidden_candidate=True))
