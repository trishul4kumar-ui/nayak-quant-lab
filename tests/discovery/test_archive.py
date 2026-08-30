from __future__ import annotations

import pytest

from quantlab.discovery.archive import CandidateArchive
from quantlab.discovery.definitions import CandidateStatus, SearchMode
from quantlab.discovery.errors import DiscoveryError
from quantlab.discovery.expression import feature_node
from quantlab.discovery.population import DiscoveryCandidate


@pytest.mark.discovery
def test_archive_keeps_losers() -> None:
    archive = CandidateArchive()
    expr = feature_node("momentum_20")
    weak = DiscoveryCandidate(
        candidate_id="cand-00-000",
        expression=expr,
        expression_hash=expr.identity_hash(),
        canonical_text=expr.canonical_text(),
        origin=SearchMode.SEEDED,
        status=CandidateStatus.FALSIFIED,
    )
    archive.add(weak)
    assert weak.expression_hash in archive.hashes()
    with pytest.raises(DiscoveryError, match="overwrite"):
        archive.refuse_overwrite(weak.expression_hash)
