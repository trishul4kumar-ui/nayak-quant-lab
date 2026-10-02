"""Explicit paper-book P&L identities. Unknown legs stay None."""

from __future__ import annotations

from quantlab.monitoring.errors import PerformanceReconciliationError
from quantlab.monitoring.models import PnLBreakdown
from quantlab.paper_oms.models import PaperAccount, PaperFill


def equity_identity(account: PaperAccount) -> None:
    expected = account.cash + account.market_value
    if abs(expected - account.equity) > 1e-6:
        raise PerformanceReconciliationError(
            f"equity identity failed: cash {account.cash} + mv "
            f"{account.market_value} != equity {account.equity}"
        )


def pnl_from_account(
    account: PaperAccount,
    *,
    beginning_equity: float,
    fills: list[PaperFill],
    deposits: float = 0.0,
) -> PnLBreakdown:
    equity_identity(account)
    long_exp = sum(max(pos.market_value, 0.0) for pos in account.positions.values())
    short_raw = sum(min(pos.market_value, 0.0) for pos in account.positions.values())
    short_exp = (
        abs(short_raw) if any(pos.quantity < 0 for pos in account.positions.values()) else None
    )
    realized = sum(pos.realized_pnl for pos in account.positions.values())
    unrealized = sum(pos.unrealized_pnl for pos in account.positions.values())
    fill_costs = sum(item.total_cost for item in fills) if fills else None
    fill_fees = sum(item.commission + item.taxes + item.fees for item in fills) if fills else None
    pnl_total = account.equity - beginning_equity - deposits
    explained = realized + unrealized
    residual = pnl_total - explained
    net_return = pnl_total / beginning_equity if beginning_equity else None
    identity_ok = abs(residual) <= 1e-4 + 1e-8 * max(1.0, abs(pnl_total))
    reserved = account.reserved_cash
    return PnLBreakdown(
        beginning_equity=beginning_equity,
        ending_equity=account.equity,
        cash=account.cash,
        reserved_cash=reserved,
        gross_exposure=account.gross_exposure,
        net_exposure=account.net_exposure,
        long_exposure=long_exp,
        short_exposure=short_exp,
        realized_pnl=realized,
        unrealized_pnl=unrealized,
        income=None,
        costs=fill_costs,
        fees=fill_fees,
        financing=None,
        adjustments=None,
        residual_pnl=residual,
        pnl_total=pnl_total,
        net_return=net_return,
        identity_ok=identity_ok,
        note=(
            "Income, financing, and tax adjustments are NOT_TESTED. "
            "Fill costs are explanatory; they are already in cash via "
            "simulated execution prices and are not subtracted twice."
        ),
    )
