from __future__ import annotations

import pytest

from quantlab.knowledge.entities import ReplicationKind, ReplicationRecord
from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.replication import add_replication

pytestmark = pytest.mark.knowledge


def test_same_snapshot_is_not_independent_replication() -> None:
    graph = KnowledgeGraph()
    with pytest.raises(KnowledgeError, match="replication_same_data"):
        add_replication(
            graph,
            ReplicationRecord(
                replication_id="R1",
                kind=ReplicationKind.EXACT_REPLICATION,
                original_hypothesis="H-MOM-001",
                original_experiment="EXP-1",
                replication_experiment="EXP-2",
                original_snapshot="SNAP-A",
                replication_snapshot="SNAP-A",
                original_protocol="next_bar",
                replication_protocol="next_bar",
            ),
        )


def test_distinct_snapshot_is_recorded() -> None:
    graph = KnowledgeGraph()
    record = add_replication(
        graph,
        ReplicationRecord(
            replication_id="R2",
            kind=ReplicationKind.TEMPORAL_REPLICATION,
            original_hypothesis="H-MOM-001",
            original_experiment="EXP-1",
            replication_experiment="EXP-2",
            original_snapshot="SNAP-A",
            replication_snapshot="SNAP-B",
            original_protocol="next_bar",
            replication_protocol="next_bar",
            dataset_difference="later window",
        ),
    )
    assert record.replication_id == "R2"
    assert len(graph.replications) == 1
