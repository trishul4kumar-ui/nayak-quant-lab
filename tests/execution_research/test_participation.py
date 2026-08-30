from __future__ import annotations

from datetime import UTC, datetime

from quantlab.domain.models import Side
from quantlab.execution_research.definition import OrderIntent
from quantlab.execution_research.fills import simulate_fill
from quantlab.execution_research.participation import max_fillable
from quantlab.execution_research.registry import get_execution_model


def test_participation_cap_limits_fill() -> None:
    assert max_fillable(1_000.0, 0.1) == 100.0
    as_of = datetime(2024, 1, 2, tzinfo=UTC)
    fill = simulate_fill(
        OrderIntent(
            intent_id="p",
            decision_time=as_of,
            security_id="NSE:TCS",
            side=Side.BUY,
            target_quantity=500.0,
            reference_price=100.0,
            max_participation=0.1,
        ),
        get_execution_model("exec_base"),
        arrival_time=as_of,
        arrival_price=100.0,
        volume=1_000.0,
        trailing_volume=1_000.0,
        trailing_vol=0.01,
    )
    assert fill.quantity == 100.0
    assert fill.remaining_quantity == 400.0
    assert fill.fill_status.value == "partially_filled"
