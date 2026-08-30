from __future__ import annotations

import pytest

from quantlab.discovery.definitions import CandidateStatus, SearchMode
from quantlab.discovery.expression import feature_node
from quantlab.discovery.lineage import build_lineage
from quantlab.discovery.population import DiscoveryCandidate


@pytest.mark.discovery
def test_lineage_records_parents() -> None:
    parent = DiscoveryCandidate(
        candidate_id="cand-00-000",
        expression=feature_node("momentum_20"),
        expression_hash=feature_node("momentum_20").identity_hash(),
        canonical_text="momentum_20",
        origin=SearchMode.SEEDED,
        status=CandidateStatus.EVALUATED,
    )
    child = parent.model_copy(
        update={
            "candidate_id": "cand-01-000",
            "generation": 1,
            "parents": [parent.expression_hash],
        }
    )
    graph = build_lineage("GP-MOM-VOL-001", [parent, child])
    assert graph.broken() is False
    assert graph.nodes[1].parents == [parent.expression_hash]
