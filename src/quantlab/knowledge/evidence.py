"""Immutable evidence. NOT_TESTED is never converted to PASS."""

from __future__ import annotations

from quantlab.domain.research import CheckResult
from quantlab.knowledge.entities import ContentOrigin, EvidenceRecord, NodeType
from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.graph import KnowledgeGraph


def add_evidence(graph: KnowledgeGraph, record: EvidenceRecord) -> EvidenceRecord:
    if record.origin is not ContentOrigin.EMPIRICAL:
        raise KnowledgeError(
            "ai_evidence_confusion: AI-generated content is not empirical evidence"
        )
    if not record.experiment_id:
        raise KnowledgeError("evidence_without_experiment")
    known = {
        node.ref_id
        for node in graph.nodes
        if node.node_type in {NodeType.EXPERIMENT, NodeType.DISCOVERY_RUN}
    }
    if known and record.experiment_id not in known:
        raise KnowledgeError("evidence_without_experiment: evidence bound to a missing experiment")
    if record.integrity_status is CheckResult.NOT_TESTED and record.metric_value is None:
        record = record.model_copy(
            update={"limitations": [*record.limitations, "metric NOT_TESTED"]}
        )
    for item in graph.evidence:
        if item.evidence_id == record.evidence_id:
            if item.model_dump(exclude={"created_at"}) != record.model_dump(exclude={"created_at"}):
                raise KnowledgeError("historical evidence is immutable")
            return item
    graph.evidence.append(record)
    return record


def mutate_evidence(graph: KnowledgeGraph, evidence_id: str) -> None:
    del graph
    raise KnowledgeError(f"historical evidence mutation refused for {evidence_id}")


def assert_evidence_experiment(record: EvidenceRecord, experiment_id: str) -> None:
    if record.experiment_id != experiment_id:
        raise KnowledgeError(
            "evidence_without_experiment: evidence attached to the wrong experiment"
        )
