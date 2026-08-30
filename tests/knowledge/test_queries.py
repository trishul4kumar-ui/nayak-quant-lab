from __future__ import annotations

import pytest
from tests.knowledge.factories import ranked_momentum

from quantlab.knowledge.memory import seed_graph
from quantlab.knowledge.query import (
    find_alpha_family,
    find_dead_ends,
    find_evidence,
    find_hypothesis,
    find_lineage,
    find_research_claims,
    find_similar_expression,
)
from quantlab.knowledge.report import knowledge_report

pytestmark = pytest.mark.knowledge


def test_seed_queries() -> None:
    graph = seed_graph()
    hypo = find_hypothesis(graph, "H-MOM-001")
    assert hypo is not None
    assert find_evidence(graph, "H-MOM-001")
    assert find_research_claims(graph, "H-MOM-001")
    assert find_dead_ends(graph)
    assert find_alpha_family(graph, "MOMENTUM")
    assert find_alpha_family(graph, "GP-MOM-VOL-001")
    path = find_lineage(graph, "hypothesis:H-MOM-001", reverse=True)
    assert path.node_ids
    report = knowledge_report(graph, "H-MOM-001")
    assert report["WHAT"]
    assert report["live_trading"] is False
    assert find_similar_expression(ranked_momentum(), ranked_momentum()).value == "identical"
