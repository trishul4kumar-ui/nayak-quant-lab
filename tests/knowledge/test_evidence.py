from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.domain.research import CheckResult
from quantlab.knowledge.entities import (
    ContentOrigin,
    EvidenceRecord,
    EvidenceType,
    KnowledgeNode,
    NodeType,
)
from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.evidence import add_evidence, assert_evidence_experiment, mutate_evidence
from quantlab.knowledge.graph import KnowledgeGraph

pytestmark = pytest.mark.knowledge


def test_historical_evidence_cannot_mutate() -> None:
    graph = KnowledgeGraph()
    graph.add_node(
        KnowledgeNode(
            node_id="experiment:E1", node_type=NodeType.EXPERIMENT, ref_id="E1"
        ).compute_hashes()
    )
    record = EvidenceRecord(
        evidence_id="EV-1",
        experiment_id="E1",
        hypothesis_id="H1",
        integrity_status=CheckResult.WARN,
        data_kind="synthetic",
    )
    add_evidence(graph, record)
    with pytest.raises(KnowledgeError, match="immutable"):
        add_evidence(graph, record.model_copy(update={"metric_value": 0.9}))
    with pytest.raises(KnowledgeError, match="mutation refused"):
        mutate_evidence(graph, "EV-1")


def test_ai_text_is_not_empirical_evidence() -> None:
    graph = KnowledgeGraph()
    graph.add_node(
        KnowledgeNode(
            node_id="experiment:E1", node_type=NodeType.EXPERIMENT, ref_id="E1"
        ).compute_hashes()
    )
    with pytest.raises(KnowledgeError, match="ai_evidence_confusion"):
        add_evidence(
            graph,
            EvidenceRecord(
                evidence_id="EV-AI",
                experiment_id="E1",
                hypothesis_id="H1",
                origin=ContentOrigin.AI_GENERATED_SUMMARY,
                result_type=EvidenceType.IN_SAMPLE_EVIDENCE,
            ),
        )


def test_evidence_on_wrong_experiment_fails() -> None:
    graph = KnowledgeGraph()
    graph.add_node(
        KnowledgeNode(
            node_id="experiment:E1", node_type=NodeType.EXPERIMENT, ref_id="E1"
        ).compute_hashes()
    )
    record = EvidenceRecord(evidence_id="EV-2", experiment_id="E-OTHER", hypothesis_id="H1")
    with pytest.raises(KnowledgeError, match="evidence_without_experiment"):
        add_evidence(graph, record)
    with pytest.raises(KnowledgeError, match="wrong experiment"):
        assert_evidence_experiment(record, "E1")


def test_not_tested_is_not_converted_to_pass() -> None:
    graph = KnowledgeGraph()
    graph.add_node(
        KnowledgeNode(
            node_id="experiment:E1", node_type=NodeType.EXPERIMENT, ref_id="E1"
        ).compute_hashes()
    )
    record = add_evidence(
        graph,
        EvidenceRecord(
            evidence_id="EV-NT",
            experiment_id="E1",
            hypothesis_id="H1",
            integrity_status=CheckResult.NOT_TESTED,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
        ),
    )
    assert record.integrity_status is CheckResult.NOT_TESTED
    assert any("NOT_TESTED" in note for note in record.limitations)
