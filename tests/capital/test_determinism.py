from __future__ import annotations

import pytest

from quantlab.capital.allocator import allocate
from quantlab.capital.library import seed_request

pytestmark = pytest.mark.capital


def test_identical_inputs_produce_identical_hashes() -> None:
    first = allocate(seed_request())
    second = allocate(seed_request())
    assert first.decision.target_weights == second.decision.target_weights
    assert first.decision.decision_hash == second.decision.decision_hash
    assert first.target.portfolio_hash == second.target.portfolio_hash
