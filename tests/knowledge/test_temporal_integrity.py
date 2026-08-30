from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.domain.research import CheckResult
from quantlab.knowledge.entities import (
    ClaimStatus,
    EvidenceRecord,
    KnowledgeNode,
    NodeType,
    ResearchClaim,
)
from quantlab.knowledge.errors import KnowledgeError
from quantlab.knowledge.evidence import add_evidence
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.status import add_claim

pytestmark = pytest.mark.knowledge


def test_future_evidence_cannot_support_earlier_claim() -> None:
    graph = KnowledgeGraph()
    graph.add_node(
        KnowledgeNode(
            node_id="experiment:E1", node_type=NodeType.EXPERIMENT, ref_id="E1"
        ).compute_hashes()
    )
    add_evidence(
        graph,
        EvidenceRecord(
            evidence_id="EV-FUTURE",
            experiment_id="E1",
            hypothesis_id="H1",
            data_kind="synthetic",
            integrity_status=CheckResult.WARN,
            created_at=datetime(2026, 6, 1, tzinfo=UTC),
            train_period="2026-06-01T00:00:00+00:00",
        ),
    )
    with pytest.raises(KnowledgeError, match="future_claim_context"):
        add_claim(
            graph,
            ResearchClaim(
                claim_id="C-EARLY",
                hypothesis_id="H1",
                statement="known as of 2024",
                support_evidence_ids=["EV-FUTURE"],
                status=ClaimStatus.PRELIMINARY,
                knowledge_as_of="2024-01-01T00:00:00+00:00",
            ),
        )
