"""Replication records. Repeating the same snapshot is not independent replication."""

from __future__ import annotations

from quantlab.knowledge.entities import ReplicationRecord
from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.graph import KnowledgeGraph


def add_replication(graph: KnowledgeGraph, record: ReplicationRecord) -> ReplicationRecord:
    if (
        record.original_snapshot
        and record.replication_snapshot
        and record.original_snapshot == record.replication_snapshot
        and record.original_protocol == record.replication_protocol
    ):
        raise KnowledgeError(
            "replication_same_data: identical snapshot/protocol is not independent"
        )
    for item in graph.replications:
        if item.replication_id == record.replication_id:
            return item
    graph.replications.append(record)
    return record
