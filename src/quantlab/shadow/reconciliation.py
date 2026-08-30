"""Shadow reconciliation wraps paper recon. Breaks are retained, never deleted."""

from __future__ import annotations

from quantlab.paper_oms.enums import ReconciliationStatus
from quantlab.paper_oms.models import PaperOMSResult
from quantlab.shadow.identity import hash_reconciliation
from quantlab.shadow.models import ShadowPortfolio, ShadowReconciliation


def reconcile_shadow(
    paper: PaperOMSResult,
    portfolio: ShadowPortfolio,
    *,
    cycle_id: str,
) -> ShadowReconciliation:
    paper_status = paper.reconciliation.status
    breaks = list(paper.reconciliation.breaks)
    unexplained = dict(paper.reconciliation.unexplained_difference)
    cash_gap = abs(paper.account.cash - portfolio.cash)
    if cash_gap > 1e-6:
        breaks.append("shadow_cash_identity")
        unexplained["cash"] = str(cash_gap)
    equity_gap = abs(paper.account.equity - portfolio.equity)
    if equity_gap > 1e-6:
        breaks.append("shadow_equity_identity")
        unexplained["equity"] = str(equity_gap)
    status = (
        ReconciliationStatus.RECONCILIATION_BREAK.value
        if breaks or paper_status is ReconciliationStatus.RECONCILIATION_BREAK
        else ReconciliationStatus.RECONCILED.value
    )
    report = ShadowReconciliation(
        report_id=f"SHREC-{cycle_id}",
        status=status,
        paper_status=paper_status.value,
        cash_difference=cash_gap,
        unexplained=unexplained,
        breaks=breaks,
        note="Shadow reconciliation wraps paper OMS recon. Not broker confirmation.",
    )
    return report.model_copy(update={"reconciliation_hash": hash_reconciliation(report)})
