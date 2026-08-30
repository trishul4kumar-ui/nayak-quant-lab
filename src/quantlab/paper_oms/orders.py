"""Paper orders from a plan. Identity is hashed; status is state-machine controlled."""

from __future__ import annotations

from quantlab.paper_oms.enums import EventType, OrderLifecycleState
from quantlab.paper_oms.events import make_event
from quantlab.paper_oms.identity import hash_order, idempotency_key
from quantlab.paper_oms.lifecycle import transition
from quantlab.paper_oms.models import OrderEvent, OrderPlan, PaperOrder, PlannedInstruction


def order_from_instruction(
    instruction: PlannedInstruction,
    plan: OrderPlan,
    *,
    account_id: str,
    decision_hash: str,
) -> PaperOrder:
    key = idempotency_key(
        decision_hash=decision_hash,
        account_id=account_id,
        snapshot_id=plan.snapshot_id,
        execution_policy_id=plan.execution_policy_id,
        plan_hash=plan.order_plan_hash + ":" + instruction.security_id,
    )
    order = PaperOrder(
        order_id="",
        idempotency_key=key,
        plan_id=plan.order_plan_id,
        plan_hash=plan.order_plan_hash,
        intent_id=instruction.intent_id,
        intent_hash=instruction.intent_hash,
        decision_hash=decision_hash,
        account_id=account_id,
        security_id=instruction.security_id,
        side=instruction.side,
        action=instruction.action,
        order_type=instruction.order_type,
        limit_price=instruction.limit_price,
        time_in_force=instruction.time_in_force,
        requested_quantity=instruction.requested_quantity,
        rounded_quantity=instruction.rounded_quantity,
        residual_quantity=instruction.residual_quantity,
        remaining_quantity=instruction.rounded_quantity,
        reference_price=instruction.reference_price,
        state=OrderLifecycleState.CREATED,
        created_at=plan.planning_time,
        arrival_time=instruction.expected_arrival,
    )
    hashed = hash_order(order)
    return order.model_copy(update={"order_hash": hashed, "order_id": f"PO-{hashed[:12]}"})


def advance(
    order: PaperOrder,
    nxt: OrderLifecycleState,
    events: list[OrderEvent],
    event_type: EventType,
    *,
    reason: str = "",
) -> PaperOrder:
    previous = order.state
    moved = transition(order, nxt, reason=reason)
    events.append(
        make_event(
            moved,
            event_type,
            previous=previous,
            new_state=moved.state,
            sequence=len(events) + 1,
            event_time=moved.created_at,
            note=reason,
        )
    )
    return moved
