from __future__ import annotations

from datetime import UTC, datetime

from quantlab.domain.models import Side
from quantlab.execution_research.definition import FillStatus, OrderIntent
from quantlab.execution_research.fills import simulate_fill
from quantlab.execution_research.registry import get_execution_model


def test_partial_fill_preserves_residual() -> None:
    as_of = datetime(2024, 1, 2, tzinfo=UTC)
    fill = simulate_fill(
        OrderIntent(
            intent_id="partial",
            decision_time=as_of,
            security_id="NSE:TCS",
            side=Side.BUY,
            target_quantity=1_000.0,
            reference_price=100.0,
            max_participation=0.05,
        ),
        get_execution_model("exec_partial"),
        arrival_time=as_of,
        arrival_price=100.0,
        volume=1_000.0,
        trailing_volume=1_000.0,
        trailing_vol=0.01,
    )
    assert fill.remaining_quantity == fill.requested_quantity - fill.quantity
    assert fill.remaining_quantity > 0
    assert fill.fill_status is FillStatus.PARTIALLY_FILLED


def test_unfilled_when_volume_unknown() -> None:
    as_of = datetime(2024, 1, 2, tzinfo=UTC)
    fill = simulate_fill(
        OrderIntent(
            intent_id="none",
            decision_time=as_of,
            security_id="NSE:TCS",
            side=Side.BUY,
            target_quantity=10.0,
            reference_price=100.0,
            max_participation=0.2,
        ),
        get_execution_model("exec_unknown_adv"),
        arrival_time=as_of,
        arrival_price=100.0,
        volume=None,
        trailing_volume=None,
        trailing_vol=None,
    )
    assert fill.quantity == 0.0
    assert fill.fill_status is FillStatus.UNFILLED
