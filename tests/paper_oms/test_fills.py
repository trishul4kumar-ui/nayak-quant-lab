from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.domain.models import Side
from quantlab.paper_oms.enums import EventType, OrderLifecycleState
from quantlab.paper_oms.errors import DuplicateOrderError
from quantlab.paper_oms.fills import apply_fill_to_order, quantity_identity
from quantlab.paper_oms.intent import intents_from_target
from quantlab.paper_oms.library import seed_account, seed_decision, seed_snapshot, seed_target
from quantlab.paper_oms.models import PaperFill
from quantlab.paper_oms.orders import order_from_instruction
from quantlab.paper_oms.planner import plan_orders
from quantlab.paper_oms.policy import resolve_policy

pytestmark = pytest.mark.paper_oms


def _order():
    plan = plan_orders(
        intents_from_target(seed_decision(), seed_target(), seed_account(), seed_snapshot()),
        seed_account(),
        seed_snapshot(),
        resolve_policy("base"),
    )
    return order_from_instruction(
        plan.instructions[0], plan, account_id="PAPER-001", decision_hash="seed-decision"
    )


def test_partial_fill_quantity_identity() -> None:
    order = _order()
    when = datetime(2024, 1, 15, tzinfo=UTC)
    fill = PaperFill(
        fill_id="PF-1",
        order_id=order.order_id,
        security_id=order.security_id,
        side=Side.BUY,
        requested_quantity=order.rounded_quantity,
        filled_quantity=order.rounded_quantity * 0.6,
        remaining_quantity=order.rounded_quantity * 0.4,
        reference_price=order.reference_price,
        arrival_price=order.reference_price,
        execution_price=order.reference_price,
        gross_notional=order.rounded_quantity * 0.6 * order.reference_price,
        arrival_time=when,
        fill_time=when,
        execution_model_id="exec_partial",
    )
    updated = apply_fill_to_order(order, fill, seen_fill_ids=set())
    assert quantity_identity(updated)
    assert updated.remaining_quantity > 0
    with pytest.raises(DuplicateOrderError):
        apply_fill_to_order(updated, fill, seen_fill_ids={"PF-1"})


def test_created_event_type_exists() -> None:
    assert EventType.ORDER_CREATED.value == "OrderCreated"
    assert OrderLifecycleState.SUBMITTED_PAPER.value == "submitted_paper"
