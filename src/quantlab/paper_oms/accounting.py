"""Paper cash and position accounting. Broken identities are FAIL."""

from __future__ import annotations

from quantlab.domain.models import Side
from quantlab.paper_oms.errors import AccountingInvariantError, InsufficientPositionError
from quantlab.paper_oms.models import CashLedger, PaperAccount, PaperFill, PaperMarketSnapshot
from quantlab.paper_oms.positions import mark_positions, upsert_position

TOL = 1e-6


def apply_fill(
    account: PaperAccount,
    fill: PaperFill,
    snapshot: PaperMarketSnapshot,
) -> PaperAccount:
    if fill.filled_quantity <= 0:
        return account
    positions = dict(account.positions)
    current = positions.get(fill.security_id)
    qty = 0.0 if current is None else current.quantity
    avg = 0.0 if current is None else current.average_cost
    realized = 0.0 if current is None else current.realized_pnl
    cash = account.cash
    purchases = 0.0 if account.ledger is None else account.ledger.purchases
    sales = 0.0 if account.ledger is None else account.ledger.sales
    fees = account.fees + fill.fees
    notional = fill.filled_quantity * fill.execution_price
    if fill.side is Side.BUY:
        new_qty = qty + fill.filled_quantity
        avg = (qty * avg + notional) / new_qty if new_qty else 0.0
        qty = new_qty
        cash -= notional
        purchases += notional
    else:
        if qty + 1e-9 < fill.filled_quantity and not account.allow_short:
            raise InsufficientPositionError(
                f"paper sell exceeds long position for {fill.security_id}"
            )
        realized += (fill.execution_price - avg) * fill.filled_quantity
        qty -= fill.filled_quantity
        cash += notional
        sales += notional
        if abs(qty) <= 1e-12:
            qty = 0.0
    reserved = max(account.reserved_cash - fill.requested_quantity * fill.reference_price, 0.0)
    if fill.side is Side.SELL:
        reserved = account.reserved_cash
    opening = account.cash if account.ledger is None else account.ledger.opening_cash
    deposits = 0.0 if account.ledger is None else account.ledger.deposits
    ledger = CashLedger(
        opening_cash=opening,
        deposits=deposits,
        purchases=purchases,
        sales=sales,
        fees=fees,
        closing_cash=cash,
    )
    positions = upsert_position(
        positions,
        fill.security_id,
        quantity=qty,
        average_cost=avg,
        realized_pnl=realized,
        price=snapshot.prices.get(fill.security_id, fill.execution_price),
        as_of=snapshot.as_of,
    )
    next_account = account.model_copy(
        update={
            "cash": cash,
            "reserved_cash": reserved,
            "available_cash": cash - reserved,
            "positions": positions,
            "fees": fees,
            "slippage": account.slippage + fill.slippage_cost,
            "impact": account.impact + fill.impact_cost,
            "ledger": ledger,
            "turnover": account.turnover + abs(notional),
        }
    )
    marked = mark_positions(next_account, snapshot)
    assert_cash_identity(marked)
    assert_equity_identity(marked)
    return marked


def reserve_buy(account: PaperAccount, notional: float) -> PaperAccount:
    reserved = account.reserved_cash + max(notional, 0.0)
    return account.model_copy(
        update={
            "reserved_cash": reserved,
            "available_cash": account.cash - reserved,
        }
    )


def assert_cash_identity(account: PaperAccount) -> None:
    ledger = account.ledger
    if ledger is None:
        return
    expected = ledger.opening_cash + ledger.deposits - ledger.purchases + ledger.sales
    if abs(expected - ledger.closing_cash) > TOL:
        raise AccountingInvariantError(
            f"cash identity failed: expected {expected} closing {ledger.closing_cash}"
        )
    if abs(ledger.closing_cash - account.cash) > TOL:
        raise AccountingInvariantError("cash ledger does not match account cash")


def assert_equity_identity(account: PaperAccount) -> None:
    expected = account.cash + account.market_value
    if abs(expected - account.equity) > TOL:
        raise AccountingInvariantError(
            f"equity identity failed: cash+mv {expected} equity {account.equity}"
        )
