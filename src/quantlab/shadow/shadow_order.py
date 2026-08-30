"""Shadow orders are distinct from paper orders and are never routable."""

from __future__ import annotations

from quantlab.paper_oms.models import PaperOrder
from quantlab.shadow.cycle import advance_order
from quantlab.shadow.enums import ShadowOrderStatus
from quantlab.shadow.models import ShadowOrder


def from_paper_order(order: PaperOrder, *, cycle_id: str) -> ShadowOrder:
    status = ShadowOrderStatus.CREATED
    status = advance_order(status, ShadowOrderStatus.VALIDATED)
    status = advance_order(status, ShadowOrderStatus.SIMULATED)
    remaining = order.remaining_quantity
    if remaining > 1e-12:
        status = advance_order(status, ShadowOrderStatus.PARTIAL)
    else:
        status = advance_order(status, ShadowOrderStatus.COMPLETED)
        status = advance_order(status, ShadowOrderStatus.RECONCILED)
    return ShadowOrder(
        shadow_order_id=f"SHD-{order.order_id}",
        intent_id=order.intent_id,
        cycle_id=cycle_id,
        security_id=order.security_id,
        side=order.side,
        quantity=order.rounded_quantity,
        filled_quantity=order.filled_quantity,
        remaining_quantity=remaining,
        residual_quantity=order.residual_quantity,
        reference_price=order.reference_price,
        arrival_time=order.arrival_time,
        expected_fill_model="paper_oms",
        execution_policy=order.plan_id,
        status=status,
        paper_order_id=order.order_id,
        routable=False,
        note="Shadow order. Not routable. Not a broker working order.",
    )
