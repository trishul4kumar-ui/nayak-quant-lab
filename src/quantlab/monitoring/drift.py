"""Target vs observed drift. The monitor never silently rebalances."""

from __future__ import annotations

from quantlab.capital.definitions import TargetPortfolio
from quantlab.monitoring.enums import DriftStatus
from quantlab.monitoring.models import DriftObservation
from quantlab.paper_oms.models import PaperAccount, PaperOMSResult


def measure_drift(
    target: TargetPortfolio,
    account: PaperAccount,
    result: PaperOMSResult,
) -> DriftObservation:
    weight_drift: dict[str, float] = {}
    quantity_drift: dict[str, float] = {}
    names = set(target.weights) | set(account.positions)
    for name in names:
        target_w = target.weights.get(name, 0.0)
        pos = account.positions.get(name)
        actual_w = pos.weight if pos is not None else 0.0
        weight_drift[name] = actual_w - target_w
        target_qty = 0.0
        price = pos.market_price if pos is not None and pos.market_price else 0.0
        if price > 0 and name in target.notional_targets:
            target_qty = target.notional_targets[name] / price
        actual_qty = pos.quantity if pos is not None else 0.0
        quantity_drift[name] = actual_qty - target_qty
    cash_target = target.cash_target * account.equity if account.equity else 0.0
    cash_drift = account.cash - cash_target
    exposure_drift = account.gross_exposure - target.gross_exposure
    unfilled: dict[str, float] = {}
    residual_orders = 0
    for order in result.orders:
        leftover = order.remaining_quantity + order.residual_quantity
        if leftover > 0:
            unfilled[order.security_id] = unfilled.get(order.security_id, 0.0) + leftover
            residual_orders += 1
    gap = sum(abs(v) for v in weight_drift.values())
    status = DriftStatus.ALIGNED if gap < 1e-6 and residual_orders == 0 else DriftStatus.DRIFTED
    return DriftObservation(
        status=status,
        weight_drift=weight_drift,
        quantity_drift=quantity_drift,
        cash_drift=cash_drift,
        exposure_drift=exposure_drift,
        implementation_gap=gap,
        unfilled_quantity=unfilled,
        residual_orders=residual_orders,
        note="Observed vs target. No automatic rebalance.",
    )
