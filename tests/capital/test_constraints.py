from __future__ import annotations

import pytest

from quantlab.capital.allocator import allocate
from quantlab.capital.constraints import refuse_silent_fallback
from quantlab.capital.errors import CapitalError, InfeasibleCapitalAllocation
from quantlab.capital.library import seed_policy, seed_request

pytestmark = pytest.mark.capital


def test_position_limit_is_not_silently_clipped() -> None:
    policy = seed_policy().model_copy(update={"max_position_weight": 0.01})
    with pytest.raises(InfeasibleCapitalAllocation) as exc:
        allocate(seed_request(), policy=policy)
    assert "max_position_weight" in exc.value.violated_constraints
    assert exc.value.current_candidate


def test_silent_fallback_is_refused() -> None:
    with pytest.raises(CapitalError, match="silent_fallback"):
        refuse_silent_fallback(seed_policy())
