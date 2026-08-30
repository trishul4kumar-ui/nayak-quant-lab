from __future__ import annotations

import pytest

from quantlab.domain.models import Side
from quantlab.paper_oms.enums import OrderAction, OrderLifecycleState
from quantlab.paper_oms.errors import InvalidOrderTransition
from quantlab.paper_oms.intent import intents_from_target
from quantlab.paper_oms.library import seed_account, seed_decision, seed_snapshot, seed_target
from quantlab.paper_oms.lifecycle import transition
from quantlab.paper_oms.orders import order_from_instruction
from quantlab.paper_oms.planner import plan_orders
from quantlab.paper_oms.policy import resolve_policy

pytestmark = pytest.mark.paper_oms


def test_intent_uses_delta_not_target_sign() -> None:
    account = seed_account()
    snapshot = seed_snapshot()
    decision = seed_decision()
    target = seed_target()
    intents = intents_from_target(decision, target, account, snapshot)
    assert intents
    assert all(item.action is OrderAction.BUY for item in intents)
    assert all(item.side is Side.BUY for item in intents)
    assert all(item.rounded_quantity > 0 for item in intents)
    held = seed_account()
    from quantlab.paper_oms.models import PaperPosition

    aaa = next(item for item in intents if item.security_id == "NSE:AAA")
    marked = held.model_copy(
        update={
            "positions": {
                "NSE:AAA": PaperPosition(
                    security_id="NSE:AAA",
                    quantity=aaa.target_quantity,
                    average_cost=100.0,
                    market_price=100.0,
                    market_value=aaa.target_quantity * 100.0,
                )
            }
        }
    )
    from quantlab.paper_oms.positions import mark_positions

    marked = mark_positions(marked, snapshot)
    second = intents_from_target(decision, target, marked, snapshot)
    aaa2 = [item for item in second if item.security_id == "NSE:AAA"]
    assert aaa2 == []


def test_rounding_residual_visible() -> None:
    intents = intents_from_target(seed_decision(), seed_target(), seed_account(), seed_snapshot())
    ccc = next(item for item in intents if item.security_id == "NSE:CCC")
    assert ccc.requested_quantity > ccc.rounded_quantity
    assert ccc.residual_quantity > 0
    assert abs(ccc.requested_quantity - ccc.rounded_quantity - ccc.residual_quantity) < 1e-9


def test_plan_is_deterministic() -> None:
    policy = resolve_policy("base")
    a = plan_orders(
        intents_from_target(seed_decision(), seed_target(), seed_account(), seed_snapshot()),
        seed_account(),
        seed_snapshot(),
        policy,
    )
    b = plan_orders(
        intents_from_target(seed_decision(), seed_target(), seed_account(), seed_snapshot()),
        seed_account(),
        seed_snapshot(),
        policy,
    )
    assert a.order_plan_hash == b.order_plan_hash
    assert a.intent_hash == b.intent_hash


def test_invalid_transition_rejected() -> None:
    policy = resolve_policy("base")
    plan = plan_orders(
        intents_from_target(seed_decision(), seed_target(), seed_account(), seed_snapshot()),
        seed_account(),
        seed_snapshot(),
        policy,
    )
    order = order_from_instruction(
        plan.instructions[0],
        plan,
        account_id="PAPER-001",
        decision_hash="seed-decision",
    )
    assert order.state is OrderLifecycleState.CREATED
    with pytest.raises(InvalidOrderTransition):
        transition(order, OrderLifecycleState.FILLED)
