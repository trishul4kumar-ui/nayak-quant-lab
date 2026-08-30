"""Reconcile target, intents, plan, orders, fills, positions, and cash. Never silent-repair."""

from __future__ import annotations

from quantlab.capital.definitions import TargetPortfolio
from quantlab.paper_oms.enums import ReconciliationStatus
from quantlab.paper_oms.fills import quantity_identity
from quantlab.paper_oms.identity import hash_reconciliation
from quantlab.paper_oms.models import (
    OrderEvent,
    PaperAccount,
    PaperFill,
    PaperOrder,
    ReconciliationReport,
    TargetPositionGap,
)

QTY_TOL = 1e-6
CASH_TOL = 1e-6
WEIGHT_TOL = 1e-8


def reconcile(
    *,
    target: TargetPortfolio,
    account: PaperAccount,
    orders: list[PaperOrder],
    fills: list[PaperFill],
    events: list[OrderEvent],
    snapshot_prices: dict[str, float],
    equity: float,
) -> ReconciliationReport:
    breaks: list[str] = []
    unexplained: dict[str, str] = {}
    order_ids = {item.order_id for item in orders}
    fill_ids = [item.fill_id for item in fills]
    if len(fill_ids) != len(set(fill_ids)):
        breaks.append("duplicate_fill")
        unexplained["duplicate_fill"] = "duplicate fill_id in run"
    for fill in fills:
        if fill.order_id not in order_ids:
            breaks.append("orphan_fill")
            unexplained[fill.fill_id] = "fill without order"
    event_orders = {item.order_id for item in events}
    for event in events:
        if event.order_id not in order_ids and not event.order_id.startswith("ACCT"):
            breaks.append("orphan_event")
            unexplained[event.event_id] = "event without order"
    sequences: dict[str, int] = {}
    for event in events:
        prev = sequences.get(event.order_id, 0)
        if event.sequence_number <= prev:
            breaks.append("event_sequence_break")
            unexplained[event.event_id] = "non-increasing sequence"
        sequences[event.order_id] = event.sequence_number
    del event_orders

    fill_by_order: dict[str, float] = {}
    for fill in fills:
        fill_by_order[fill.order_id] = fill_by_order.get(fill.order_id, 0.0) + fill.filled_quantity
    fill_difference: dict[str, float] = {}
    for order in orders:
        if not quantity_identity(order):
            breaks.append("quantity_mismatch")
            unexplained[order.order_id] = "requested ≠ filled+remaining+cancelled+expired"
        expected = fill_by_order.get(order.order_id, 0.0)
        if abs(expected - order.filled_quantity) > QTY_TOL:
            fill_difference[order.security_id] = expected - order.filled_quantity
            breaks.append("order_fill_mismatch")

    gaps: list[TargetPositionGap] = []
    target_difference: dict[str, float] = {}
    position_difference: dict[str, float] = {}
    names = sorted(set(target.weights) | set(account.positions))
    for name in names:
        price = snapshot_prices.get(name, 0.0)
        target_w = float(target.weights.get(name, 0.0))
        target_q = (target.notional_targets.get(name, target_w * equity) / price) if price else 0.0
        pos = account.positions.get(name)
        actual_q = 0.0 if pos is None else pos.quantity
        actual_w = 0.0 if pos is None else pos.weight
        qty_err = actual_q - target_q
        w_err = actual_w - target_w
        notional_err = qty_err * price
        gaps.append(
            TargetPositionGap(
                security_id=name,
                target_weight=target_w,
                actual_weight=actual_w,
                weight_error=w_err,
                target_quantity=target_q,
                actual_quantity=actual_q,
                quantity_error=qty_err,
                notional_error=notional_err,
            )
        )
        if abs(qty_err) > QTY_TOL:
            target_difference[name] = qty_err
            position_difference[name] = qty_err

    cash_difference = 0.0
    if account.ledger is not None:
        cash_difference = account.cash - account.ledger.closing_cash
        if abs(cash_difference) > CASH_TOL:
            breaks.append("cash_mismatch")

    residual_explained = all(
        abs(gap.quantity_error) <= abs(order_residual(orders, gap.security_id)) + QTY_TOL
        for gap in gaps
    )
    unexplained_target = not residual_explained and bool(target_difference)
    if unexplained_target:
        breaks.append("target_position_mismatch")
        unexplained["target"] = "position gap exceeds residual/unfilled quantity"

    status = ReconciliationStatus.RECONCILED
    if breaks:
        status = ReconciliationStatus.RECONCILIATION_BREAK
    report = ReconciliationReport(
        report_id="",
        status=status,
        target_difference=target_difference,
        order_difference={},
        fill_difference=fill_difference,
        position_difference=position_difference,
        cash_difference=cash_difference,
        unexplained_difference=unexplained,
        breaks=sorted(set(breaks)),
        gaps=gaps,
        note=(
            "RECONCILED with visible residuals"
            if status is ReconciliationStatus.RECONCILED
            else "RECONCILIATION_BREAK retained; not silently repaired"
        ),
    )
    hashed = hash_reconciliation(report)
    return report.model_copy(
        update={"reconciliation_hash": hashed, "report_id": f"REC-{hashed[:12]}"}
    )


def order_residual(orders: list[PaperOrder], security_id: str) -> float:
    total = 0.0
    for order in orders:
        if order.security_id != security_id:
            continue
        total += order.remaining_quantity + order.residual_quantity
        total += order.cancelled_quantity + order.expired_quantity
    return total
