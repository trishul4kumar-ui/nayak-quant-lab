from __future__ import annotations

from datetime import UTC, datetime

from quantlab.domain.models import Side
from quantlab.execution_research.definition import OrderIntent
from quantlab.execution_research.fills import simulate_fill
from quantlab.execution_research.registry import get_execution_model


def test_buy_and_sell_slippage_are_adverse() -> None:
    model = get_execution_model("exec_high_slippage")
    as_of = datetime(2024, 1, 2, tzinfo=UTC)
    buy = simulate_fill(
        OrderIntent(
            intent_id="b",
            decision_time=as_of,
            security_id="NSE:TCS",
            side=Side.BUY,
            target_quantity=50.0,
            reference_price=100.0,
            max_participation=1.0,
        ),
        model,
        arrival_time=as_of,
        arrival_price=100.0,
        volume=1_000_000.0,
        trailing_volume=1_000_000.0,
        trailing_vol=0.01,
    )
    sell = simulate_fill(
        OrderIntent(
            intent_id="s",
            decision_time=as_of,
            security_id="NSE:TCS",
            side=Side.SELL,
            target_quantity=50.0,
            reference_price=100.0,
            max_participation=1.0,
        ),
        model,
        arrival_time=as_of,
        arrival_price=100.0,
        volume=1_000_000.0,
        trailing_volume=1_000_000.0,
        trailing_vol=0.01,
    )
    assert buy.execution_price >= 100.0
    assert sell.execution_price <= 100.0
    assert buy.slippage_cost > 0
    assert sell.slippage_cost > 0
    assert buy.total_cost > 0
    assert sell.total_cost > 0
