"""Paper TCA and lifecycle reports. Deterministic and auditable."""

from __future__ import annotations

from quantlab.domain.models import Side
from quantlab.domain.research import CheckResult
from quantlab.paper_oms.models import (
    OMSRun,
    PaperAccount,
    PaperFill,
    PaperOMSResult,
    PaperOrder,
    ReconciliationReport,
    TCAReport,
)


def tca_report(
    *,
    target_notional: float,
    fills: list[PaperFill],
    residual_notional: float,
) -> TCAReport:
    filled_notional = sum(item.gross_notional for item in fills)
    spread = sum(item.spread_cost for item in fills)
    slip = sum(item.slippage_cost for item in fills)
    impact = sum(item.impact_cost for item in fills)
    commission = sum(item.commission for item in fills)
    other_fees = sum(item.taxes for item in fills)
    drag = spread + slip + impact + commission + other_fees
    shortfall = 0.0
    valid = True
    for fill in fills:
        if fill.filled_quantity <= 0:
            continue
        if fill.arrival_price <= 0 or fill.execution_price <= 0:
            valid = False
            break
        signed = 1.0 if fill.side is Side.BUY else -1.0
        shortfall += signed * (fill.execution_price - fill.arrival_price) * fill.filled_quantity
        shortfall += fill.commission + fill.taxes
    return TCAReport(
        gross_target_notional=target_notional,
        filled_notional=filled_notional,
        spread_drag=spread,
        slippage_drag=slip,
        impact_drag=impact,
        commission=commission,
        other_specified_fees=other_fees,
        total_execution_drag=drag,
        residual_target=residual_notional,
        implementation_shortfall=shortfall if valid and fills else None,
        implementation_shortfall_status=(
            CheckResult.PASS if valid and fills else CheckResult.NOT_TESTED
        ),
        note=(
            "Implementation shortfall vs arrival snapshot price. "
            "Simulated. Taxes unspecified remain 0 with NOT_TESTED provenance on tax legs."
        ),
    )


def result_report(result: PaperOMSResult) -> dict[str, object]:
    recon: ReconciliationReport = result.reconciliation
    run: OMSRun = result.run
    account: PaperAccount = result.account
    return {
        "oms_run_id": run.oms_run_id,
        "status": run.status.value,
        "decision_hash": run.decision_hash,
        "order_plan_hash": run.order_plan_hash,
        "run_hash": run.run_hash,
        "order_count": run.order_count,
        "fill_count": run.fill_count,
        "reconciliation": recon.status.value,
        "breaks": recon.breaks,
        "cash": account.cash,
        "equity": account.equity,
        "market_value": account.market_value,
        "tca": result.tca.model_dump(mode="json"),
        "exceptions": result.exceptions,
        "live_trading": False,
        "note": "Paper report. Fills are simulated.",
    }


def lifecycle_rows(orders: list[PaperOrder]) -> list[dict[str, object]]:
    return [
        {
            "order_id": item.order_id,
            "security_id": item.security_id,
            "side": item.side.value,
            "state": item.state.value,
            "requested": item.requested_quantity,
            "rounded": item.rounded_quantity,
            "filled": item.filled_quantity,
            "remaining": item.remaining_quantity,
            "residual": item.residual_quantity,
        }
        for item in orders
    ]
