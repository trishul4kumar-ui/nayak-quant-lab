from __future__ import annotations

import pytest

from quantlab.capital.allocator import allocate
from quantlab.capital.definitions import AbstentionCode, CapitalAllocationState, DrawdownState
from quantlab.capital.drawdown import classify_drawdown
from quantlab.capital.library import seed_policy, seed_request

pytestmark = pytest.mark.capital


def test_drawdown_thresholds_come_from_policy() -> None:
    limits = seed_policy().drawdown_limits
    assert classify_drawdown(0.04, limits) is DrawdownState.NORMAL
    assert classify_drawdown(0.06, limits) is DrawdownState.CAUTION
    assert classify_drawdown(0.12, limits) is DrawdownState.DEFENSIVE
    assert classify_drawdown(0.20, limits) is DrawdownState.HALTED


def test_halt_does_not_open_new_exposure() -> None:
    result = allocate(seed_request(drawdown=0.20))
    assert result.decision.abstention_code is AbstentionCode.DRAWDOWN_HALT
    assert result.decision.capital_state is CapitalAllocationState.HALT
    assert result.decision.target_weights == {}
