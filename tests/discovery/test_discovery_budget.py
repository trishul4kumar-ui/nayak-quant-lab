from __future__ import annotations

import pytest

from quantlab.discovery.errors import DiscoveryError
from quantlab.discovery.search import SearchBudget, assert_budget_frozen


@pytest.mark.discovery
def test_budget_freeze() -> None:
    frozen = SearchBudget(population_size=8, n_generations=3, max_candidates=24, seed=7)
    assert_budget_frozen(frozen, frozen.model_copy())
    with pytest.raises(DiscoveryError, match="mutated"):
        assert_budget_frozen(frozen, frozen.model_copy(update={"n_generations": 99}))
