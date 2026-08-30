from __future__ import annotations

import pytest

from quantlab.capital.allocator import allocate
from quantlab.capital.definitions import AbstentionCode, LiquidityStatus
from quantlab.capital.library import seed_policy, seed_request
from quantlab.capital.liquidity import classify_name

pytestmark = pytest.mark.capital


def test_unknown_liquidity_is_not_infinite() -> None:
    status = classify_name(None, 1000.0, seed_policy().liquidity_policy)
    assert status is LiquidityStatus.UNKNOWN


def test_unknown_liquidity_abstains_under_strict_policy() -> None:
    result = allocate(seed_request(liquidity_adv={}))
    assert result.decision.abstention_code is AbstentionCode.UNKNOWN_LIQUIDITY
    assert result.decision.decision_status.value == "abstain"
