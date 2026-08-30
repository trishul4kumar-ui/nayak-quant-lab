"""Paper fill application. Remaining quantity is first-class."""

from __future__ import annotations

from quantlab.paper_oms.enums import RemainderFate
from quantlab.paper_oms.errors import DuplicateOrderError
from quantlab.paper_oms.models import PaperFill, PaperOrder


def apply_fill_to_order(
    order: PaperOrder,
    fill: PaperFill,
    *,
    seen_fill_ids: set[str],
    remainder: RemainderFate = RemainderFate.OPEN,
) -> PaperOrder:
    if fill.fill_id in seen_fill_ids:
        raise DuplicateOrderError(f"duplicate paper fill {fill.fill_id}")
    if fill.order_id != order.order_id:
        raise DuplicateOrderError("fill does not belong to this paper order")
    filled = order.filled_quantity + fill.filled_quantity
    remaining = max(
        order.rounded_quantity - filled - order.cancelled_quantity - order.expired_quantity,
        0.0,
    )
    cancelled = order.cancelled_quantity
    expired = order.expired_quantity
    fate = remainder
    if remaining <= 1e-12:
        remaining = 0.0
        fate = RemainderFate.FILLED
    elif remainder is RemainderFate.CANCELLED_REMAINDER:
        cancelled = remaining
        remaining = 0.0
    elif remainder is RemainderFate.EXPIRED_REMAINDER:
        expired = remaining
        remaining = 0.0
    return order.model_copy(
        update={
            "filled_quantity": filled,
            "remaining_quantity": remaining,
            "cancelled_quantity": cancelled,
            "expired_quantity": expired,
            "remainder_fate": fate,
            "fill_time": fill.fill_time,
        }
    )


def quantity_identity(order: PaperOrder) -> bool:
    total = (
        order.filled_quantity
        + order.remaining_quantity
        + order.cancelled_quantity
        + order.expired_quantity
    )
    return abs(total - order.rounded_quantity) <= 1e-8
