from __future__ import annotations

import pytest

from quantlab.orchestration.registry import get_search_space
from quantlab.orchestration.search_space import expand_grid


@pytest.mark.orchestration
def test_grid_records_every_cell() -> None:
    space = get_search_space("mom_lookback_cost")
    candidates = expand_grid(space)
    assert len(candidates) == space.size()
    assert space.size() == 4
    ids = {c.candidate_id for c in candidates}
    assert len(ids) == len(candidates)
    assert all(not c.hidden for c in candidates)
