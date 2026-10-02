"""Security-level accounting attribution. Residual stays visible."""

from __future__ import annotations

from quantlab.domain.research import CheckResult
from quantlab.monitoring.enums import AttributionMethod
from quantlab.monitoring.models import AttributionResult, PnLBreakdown, SecurityContribution
from quantlab.paper_oms.models import PaperAccount, PaperFill


def security_attribution(
    account: PaperAccount,
    pnl: PnLBreakdown,
    fills: list[PaperFill],
) -> AttributionResult:
    costs: dict[str, float] = {}
    turnover: dict[str, float] = {}
    for fill in fills:
        costs[fill.security_id] = costs.get(fill.security_id, 0.0) + fill.total_cost
        turnover[fill.security_id] = turnover.get(fill.security_id, 0.0) + abs(fill.gross_notional)
    denom = pnl.beginning_equity if pnl.beginning_equity else 1.0
    rows: list[SecurityContribution] = []
    explained = 0.0
    for pos in account.positions.values():
        piece = pos.realized_pnl + pos.unrealized_pnl
        explained += piece
        exposure = abs(pos.market_value) / denom if denom else 0.0
        rows.append(
            SecurityContribution(
                security_id=pos.security_id,
                pnl=piece,
                return_contribution=piece / denom,
                realized=pos.realized_pnl,
                unrealized=pos.unrealized_pnl,
                cost=costs.get(pos.security_id, 0.0),
                turnover=turnover.get(pos.security_id, 0.0),
                exposure_share=exposure,
            )
        )
    residual = pnl.pnl_total - explained
    recon_ok = abs(residual - pnl.residual_pnl) <= 1e-6 + 1e-8 * max(1.0, abs(pnl.pnl_total))
    return AttributionResult(
        method=AttributionMethod.EXACT_ACCOUNTING,
        total=pnl.pnl_total,
        residual=residual,
        contributions=rows,
        status=CheckResult.PASS if recon_ok else CheckResult.FAIL,
        note=(
            "Σ security contribution + residual = total P&L. "
            "Residual is visible; it is never hidden."
        ),
    )
