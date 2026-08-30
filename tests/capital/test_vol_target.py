from __future__ import annotations

import pytest

from quantlab.capital.definitions import VolTargetStatus
from quantlab.capital.library import seed_covariance
from quantlab.capital.volatility_target import target_volatility

pytestmark = pytest.mark.capital


def test_vol_target_does_not_exceed_leverage() -> None:
    weights = {"NSE:AAA": 0.5, "NSE:BBB": 0.3, "NSE:CCC": 0.2}
    result = target_volatility(weights, seed_covariance(), target=0.90, max_leverage=1.0)
    assert result.status is VolTargetStatus.TARGET_UNACHIEVABLE
    assert result.scale <= 1.0 + 1e-12
    assert sum(abs(v) for v in result.weights.values()) <= 1.0 + 1e-9


def test_missing_covariance_is_not_tested() -> None:
    result = target_volatility({"A": 1.0}, None, 0.15, 1.0)
    assert result.status is VolTargetStatus.NOT_TESTED
    assert result.estimated_vol is None
