from __future__ import annotations

import pytest

from quantlab.capital.allocator import allocate
from quantlab.capital.library import seed_request
from quantlab.domain.research import CheckResult
from quantlab.research.integrity import evaluate_integrity

pytestmark = pytest.mark.capital


def test_future_leak_flags_fail() -> None:
    report = evaluate_integrity(
        bars=[],
        states=[],
        as_of_times=[],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=False,
        n_experiments_in_family=1,
        used_ml=False,
        future_expected_return=True,
        future_liquidity=True,
        future_drawdown_state=True,
        silent_fallback=True,
        hidden_constraint_relaxation=True,
    )
    assert report.checks["future_expected_return"] is CheckResult.FAIL
    assert report.checks["future_liquidity"] is CheckResult.FAIL
    assert report.checks["future_drawdown_state"] is CheckResult.FAIL
    assert report.checks["silent_fallback"] is CheckResult.FAIL
    assert report.checks["hidden_constraint_relaxation"] is CheckResult.FAIL


def test_allocator_records_no_leak_on_seed_path() -> None:
    result = allocate(seed_request())
    assert result.integrity.checks["future_capital_input"] is CheckResult.PASS
    assert result.integrity.checks["synthetic_capital_overpromotion"] is CheckResult.PASS
    assert result.integrity.checks["live_trading_disabled"] is CheckResult.PASS
