"""Target portfolio → order intents. Never infers BUY from target_weight sign alone."""

from __future__ import annotations

import math

from quantlab.capital.definitions import DecisionStatus, InvestmentDecision, TargetPortfolio
from quantlab.domain.models import Side
from quantlab.paper_oms.enums import OrderAction, RoundingPolicy
from quantlab.paper_oms.errors import OrderPlanningError
from quantlab.paper_oms.identity import hash_intent
from quantlab.paper_oms.models import OrderIntent, PaperAccount, PaperMarketSnapshot


def _quantity(notional: float, price: float) -> float:
    if price <= 0:
        raise OrderPlanningError("reference price must be positive")
    return notional / price


def _round_lot(quantity: float, lot: int, policy: RoundingPolicy) -> tuple[float, float]:
    requested = abs(float(quantity))
    size = max(int(lot), 1)
    if policy is RoundingPolicy.FLOOR_LOT:
        rounded = math.floor(requested / size + 1e-12) * size
    else:
        raise OrderPlanningError(f"unsupported rounding policy {policy}")
    residual = requested - rounded
    return rounded, residual


def _action(current_qty: float, target_qty: float, delta: float) -> OrderAction:
    if abs(delta) <= 1e-12:
        return OrderAction.NO_ACTION
    if abs(current_qty) <= 1e-12 and target_qty > 0:
        return OrderAction.BUY
    if abs(target_qty) <= 1e-12 and current_qty > 0:
        return OrderAction.EXIT
    if delta > 0:
        return OrderAction.INCREASE if current_qty > 0 else OrderAction.BUY
    if current_qty + delta >= -1e-12:
        return OrderAction.DECREASE if current_qty + delta > 1e-12 else OrderAction.EXIT
    return OrderAction.SELL


def intents_from_target(
    decision: InvestmentDecision,
    target: TargetPortfolio,
    account: PaperAccount,
    snapshot: PaperMarketSnapshot,
    *,
    lot_size: int = 1,
    min_trade_quantity: float = 0.0,
    rounding: RoundingPolicy = RoundingPolicy.FLOOR_LOT,
) -> list[OrderIntent]:
    if target.decision_id != decision.decision_id:
        raise OrderPlanningError("target_portfolio is not the child of this investment decision")
    if decision.decision_status in {DecisionStatus.REJECTED, DecisionStatus.ABSTAIN}:
        return []
    equity = account.equity if account.equity > 0 else account.cash
    names = sorted(set(target.weights) | set(account.positions) | set(snapshot.prices))
    intents: list[OrderIntent] = []
    for name in names:
        price = snapshot.prices.get(name)
        if price is None or price <= 0:
            if abs(target.weights.get(name, 0.0)) > 1e-12:
                raise OrderPlanningError(f"missing PIT price for {name}")
            continue
        target_w = float(target.weights.get(name, 0.0))
        position = account.positions.get(name)
        current_qty = 0.0 if position is None else float(position.quantity)
        current_w = (current_qty * price / equity) if equity > 0 else 0.0
        if name in target.notional_targets and target.notional_targets[name] != 0:
            target_qty = _quantity(float(target.notional_targets[name]), price)
        else:
            target_qty = _quantity(target_w * equity, price)
        delta = target_qty - current_qty
        action = _action(current_qty, target_qty, delta)
        if action is OrderAction.NO_ACTION:
            continue
        if target_qty < -1e-12 and not account.allow_short:
            raise OrderPlanningError("shorting is not silently enabled")
        requested = abs(delta)
        lot = snapshot.lot_size.get(name, lot_size)
        rounded, residual = _round_lot(requested, lot, rounding)
        if rounded < min_trade_quantity or rounded <= 0:
            continue
        side = Side.BUY if delta > 0 else Side.SELL
        intent = OrderIntent(
            intent_id="",
            decision_id=decision.decision_id,
            decision_hash=decision.decision_hash,
            target_portfolio_id=target.portfolio_id,
            target_portfolio_hash=target.portfolio_hash,
            capital_policy_id=decision.capital_policy_id,
            experiment_id=decision.experiment_id,
            snapshot_id=snapshot.snapshot_id,
            as_of=snapshot.as_of,
            security_id=name,
            side=side,
            action=action,
            target_weight=target_w,
            current_weight=current_w,
            weight_delta=target_w - current_w,
            target_quantity=target_qty,
            current_quantity=current_qty,
            delta_quantity=delta,
            estimated_notional=rounded * price,
            requested_quantity=requested,
            rounded_quantity=rounded,
            residual_quantity=residual,
            residual_notional=residual * price,
            rounding_policy=rounding,
            reference_price=price,
        )
        hashed = hash_intent(intent)
        intents.append(
            intent.model_copy(update={"intent_hash": hashed, "intent_id": f"INT-{hashed[:12]}"})
        )
    return intents
