"""Shadow fills wrap paper fills. Residuals stay visible. Never broker-confirmed."""

from __future__ import annotations

from quantlab.paper_oms.models import PaperFill
from quantlab.shadow.models import ShadowFill


def from_paper_fill(fill: PaperFill, *, cycle_id: str, shadow_order_id: str) -> ShadowFill:
    other = fill.taxes + fill.fees
    net = fill.gross_notional + fill.total_cost
    return ShadowFill(
        shadow_fill_id=f"SHF-{fill.fill_id}",
        shadow_order_id=shadow_order_id,
        cycle_id=cycle_id,
        security_id=fill.security_id,
        side=fill.side,
        reference_price=fill.reference_price,
        execution_price=fill.execution_price,
        spread_cost=fill.spread_cost,
        slippage_cost=fill.slippage_cost,
        impact_cost=fill.impact_cost,
        commission=fill.commission,
        other_cost=other,
        gross_notional=fill.gross_notional,
        net_notional=net,
        filled_quantity=fill.filled_quantity,
        residual_quantity=fill.remaining_quantity,
        fill_time=fill.fill_time,
        paper_fill_id=fill.fill_id,
        broker_confirmed=False,
        note="Simulated shadow fill. Not broker-confirmed. Not a live execution.",
    )
