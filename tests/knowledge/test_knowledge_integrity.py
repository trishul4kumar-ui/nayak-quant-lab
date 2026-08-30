from __future__ import annotations

import pytest
from tests.knowledge.factories import integrity_report

from quantlab.domain.research import CheckResult
from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.memory import seed_graph

pytestmark = pytest.mark.knowledge


def test_knowledge_integrity_flags_fail_closed() -> None:
    report = integrity_report(ai_evidence_confusion=True, synthetic_evidence_overpromotion=True)
    assert report.checks["ai_evidence_confusion"] is CheckResult.FAIL
    assert report.checks["synthetic_evidence_overpromotion"] is CheckResult.FAIL
    assert report.failed()


def test_delete_failed_candidate_fails() -> None:
    graph = seed_graph()
    with pytest.raises(KnowledgeError, match="candidate_history_deleted"):
        graph.delete_node("dead-end:DEAD_END-042")
    assert any(item.node_id == "dead-end:DEAD_END-042" for item in graph.nodes)


def test_empty_graph_delete_still_fails() -> None:
    with pytest.raises(KnowledgeError, match="candidate_history_deleted"):
        KnowledgeGraph().delete_node("anything")
