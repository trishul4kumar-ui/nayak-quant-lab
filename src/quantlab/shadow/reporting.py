"""App-facing shadow reports. Not live. Not broker-confirmed."""

from __future__ import annotations

from typing import Any

from quantlab.shadow.models import ShadowResult


def result_report(result: ShadowResult) -> dict[str, Any]:
    residuals = [
        {
            "shadow_order_id": item.shadow_order_id,
            "remaining": item.remaining_quantity,
            "residual": item.residual_quantity,
            "status": item.status.value,
        }
        for item in result.orders
        if item.remaining_quantity > 1e-12 or item.residual_quantity > 1e-12
    ]
    return {
        "cycle_id": result.cycle.cycle_id,
        "requested_mode": result.cycle.requested_mode.value,
        "mode": result.cycle.mode.value,
        "status": result.cycle.status.value,
        "production_run": result.cycle.production_run,
        "session": result.session.value,
        "freshness_age_ms": result.freshness.age_ms,
        "stale": result.freshness.stale,
        "orders": len(result.orders),
        "fills": len(result.fills),
        "residuals": residuals,
        "cash": result.portfolio.cash,
        "equity": result.portfolio.equity,
        "recon": result.reconciliation.status,
        "replay": result.replay.value if result.replay else "",
        "live_trading": False,
        "shadow_mode": True,
        "broker_routing_enabled": False,
        "live_order_submission_enabled": False,
        "result_kind": result.result_kind.value,
        "note": result.note,
        "scorecard": result.scorecard.model_dump(mode="json"),
        "integrity_failed": result.integrity.failed(),
    }
