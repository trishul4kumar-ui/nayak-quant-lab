from __future__ import annotations

import pytest

from quantlab.capital.allocator import allocate
from quantlab.capital.library import seed_request

pytestmark = pytest.mark.capital


def test_provenance_records_identities() -> None:
    result = allocate(seed_request())
    assert result.decision.snapshot_id == "seed"
    assert result.decision.capital_policy_id == "CAP-RESEARCH-001"
    assert result.decision.portfolio_spec_id == "mom20_topn"
    assert result.decision.software_version
    assert result.decision.knowledge_snapshot_id == "KS-SEED-001"
    assert result.decision.decision_hash
