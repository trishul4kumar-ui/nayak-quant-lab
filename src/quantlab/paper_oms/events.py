"""Immutable order events. Sequence is auditable."""

from __future__ import annotations

from datetime import datetime

from quantlab.backtest.spec import config_hash
from quantlab.paper_oms.enums import EventType, OrderLifecycleState
from quantlab.paper_oms.models import OrderEvent, PaperOrder


def make_event(
    order: PaperOrder,
    event_type: EventType,
    *,
    previous: OrderLifecycleState | None,
    new_state: OrderLifecycleState,
    sequence: int,
    event_time: datetime,
    causation_id: str = "",
    correlation_id: str = "",
    note: str = "",
) -> OrderEvent:
    payload = config_hash(
        {
            "order_id": order.order_id,
            "event_type": event_type.value,
            "sequence": sequence,
            "previous": None if previous is None else previous.value,
            "new": new_state.value,
            "order_hash": order.order_hash,
        }
    )
    return OrderEvent(
        event_id=f"EVT-{payload[:12]}-{sequence}",
        order_id=order.order_id,
        event_type=event_type,
        event_time=event_time,
        sequence_number=sequence,
        previous_state=previous,
        new_state=new_state,
        payload_hash=payload,
        causation_id=causation_id or order.intent_id,
        correlation_id=correlation_id or order.idempotency_key,
        note=note,
    )
