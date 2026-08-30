"""Order lifecycle state machine. Invalid transitions raise; they are never coerced."""

from __future__ import annotations

from quantlab.paper_oms.enums import ALLOWED_TRANSITIONS, OrderLifecycleState
from quantlab.paper_oms.errors import InvalidOrderTransition
from quantlab.paper_oms.models import PaperOrder


def can_transition(current: OrderLifecycleState, nxt: OrderLifecycleState) -> bool:
    return nxt in ALLOWED_TRANSITIONS.get(current, frozenset())


def transition(order: PaperOrder, nxt: OrderLifecycleState, *, reason: str = "") -> PaperOrder:
    if not can_transition(order.state, nxt):
        raise InvalidOrderTransition(f"invalid paper order transition {order.state} → {nxt}")
    update: dict[str, object] = {"state": nxt}
    if reason:
        update["rejection_reason"] = reason
    return order.model_copy(update=update)
