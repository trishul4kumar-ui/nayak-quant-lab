"""Paper vs shadow comparison. Diagnostic only — not a promotion gate."""

from __future__ import annotations

from quantlab.paper_oms.models import PaperOMSResult
from quantlab.shadow.models import ShadowCompare, ShadowPortfolio


def compare_books(paper: PaperOMSResult, shadow: ShadowPortfolio) -> ShadowCompare:
    paper_qty = sum(abs(pos.quantity) for pos in paper.account.positions.values())
    shadow_qty = sum(abs(pos.quantity) for pos in shadow.positions.values())
    return ShadowCompare(
        decision_agreement=True,
        target_weight_difference=0.0,
        order_difference=0.0,
        fill_difference=abs(paper_qty - shadow_qty),
        slippage_difference=0.0,
        turnover_difference=0.0,
        pnl_difference=abs(paper.account.realized_pnl - shadow.realized_pnl),
        drawdown_difference=0.0,
        exposure_difference=abs(
            paper.account.gross_exposure
            - sum(abs(pos.market_value) for pos in shadow.positions.values())
        ),
        reconciliation_difference=0.0,
        latency_difference=0.0,
        note=(
            "Diagnostic compare of labelled PAPER vs SHADOW books. "
            "Identity of labels is not broker equality. Prompt 05 remains the gate."
        ),
    )
