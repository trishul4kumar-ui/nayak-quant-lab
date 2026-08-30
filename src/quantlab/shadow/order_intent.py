"""Map Prompt 18 intents onto cycle-scoped shadow intents. Δq remains authoritative."""

from __future__ import annotations

from quantlab.paper_oms.models import OrderIntent
from quantlab.shadow.models import ShadowIntent


def from_paper_intent(intent: OrderIntent, *, cycle_id: str) -> ShadowIntent:
    return ShadowIntent(
        intent_id=f"SHI-{intent.intent_id}",
        cycle_id=cycle_id,
        security_id=intent.security_id,
        side=intent.side,
        target_qty=intent.target_quantity,
        current_qty=intent.current_quantity,
        delta_qty=intent.delta_quantity,
        reference_price=intent.reference_price,
        notional=intent.estimated_notional,
        reason="delta_quantity = target_qty - current_qty",
        decision_hash=intent.decision_hash,
        target_hash=intent.target_portfolio_hash,
        timestamp=intent.as_of,
        paper_intent_id=intent.intent_id,
    )
