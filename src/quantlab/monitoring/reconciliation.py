"""Monitoring reconciliation. Never silently repair a break."""

from __future__ import annotations

from quantlab.monitoring.models import AttributionResult, PnLBreakdown


def reconcile_pnl(pnl: PnLBreakdown) -> list[str]:
    breaks: list[str] = []
    if not pnl.identity_ok:
        breaks.append("pnl_reconciliation_break")
    expected = pnl.realized_pnl + pnl.unrealized_pnl
    if abs(pnl.pnl_total - expected - pnl.residual_pnl) > 1e-6:
        breaks.append("hidden_residual")
    return breaks


def reconcile_attribution(pnl: PnLBreakdown, attr: AttributionResult) -> list[str]:
    explained = sum(row.pnl for row in attr.contributions)
    if abs(explained + attr.residual - attr.total) > 1e-6:
        return ["attribution_reconciliation_break"]
    if abs(attr.total - pnl.pnl_total) > 1e-6:
        return ["attribution_reconciliation_break"]
    return []
