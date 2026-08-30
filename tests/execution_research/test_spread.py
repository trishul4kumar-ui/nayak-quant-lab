from __future__ import annotations

from datetime import UTC, datetime

from quantlab.domain.models import Side
from quantlab.execution_research.definition import OrderIntent
from quantlab.execution_research.fills import simulate_fill
from quantlab.execution_research.registry import get_execution_model
from quantlab.execution_research.spread import spread_bps


def _intent(side: Side) -> OrderIntent:
    return OrderIntent(
        intent_id="t1",
        decision_time=datetime(2024, 1, 2, tzinfo=UTC),
        security_id="NSE:TCS",
        side=side,
        target_quantity=100.0,
        reference_price=100.0,
        max_participation=1.0,
    )


def test_fixed_spread_is_configured() -> None:
    bps, status, _check, _note = spread_bps(
        get_execution_model("exec_base"),
        volume=1_000_000.0,
        trailing_volume=1_000_000.0,
        trailing_vol=0.01,
    )
    assert bps == 5.0
    assert status.value == "configured"


def test_historical_bid_ask_is_not_tested() -> None:
    bps, status, check, _note = spread_bps(
        get_execution_model("exec_bid_ask"),
        volume=1_000_000.0,
        trailing_volume=1_000_000.0,
        trailing_vol=0.01,
    )
    assert bps is None
    assert status.value == "not_tested"
    assert check.value == "not_tested"


def test_buy_spread_does_not_improve() -> None:
    fill = simulate_fill(
        _intent(Side.BUY),
        get_execution_model("exec_wide_spread"),
        arrival_time=datetime(2024, 1, 2, tzinfo=UTC),
        arrival_price=100.0,
        volume=1_000_000.0,
        trailing_volume=1_000_000.0,
        trailing_vol=0.01,
    )
    assert fill.execution_price >= 100.0
    assert fill.spread_cost > 0
