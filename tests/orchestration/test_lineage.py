from __future__ import annotations

import pytest

from quantlab.orchestration.errors import OrchestrationError
from quantlab.orchestration.lineage import assert_lineage_intact, build_graph


@pytest.mark.orchestration
def test_lineage_graph_contains_family() -> None:
    graph = build_graph(
        hypothesis_id="H-MOM-001",
        family_id="MOM-FAMILY-001",
        candidate_ids=["c1", "c2"],
        parent_experiment="EXP-MOM-001",
    )
    assert "H-MOM-001" in graph.ids()
    assert "c1" in graph.ids()
    assert_lineage_intact(graph)


@pytest.mark.orchestration
def test_deleted_parent_is_a_break() -> None:
    graph = build_graph(
        hypothesis_id="H-MOM-001",
        family_id="MOM-FAMILY-001",
        candidate_ids=["c1"],
    )
    with pytest.raises(OrchestrationError, match="lineage"):
        assert_lineage_intact(graph, deleted_parent="MOM-FAMILY-001")
