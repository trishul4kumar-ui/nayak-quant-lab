"""Assemble a performance snapshot from paper books."""

from __future__ import annotations

from datetime import datetime

from quantlab.monitoring.identity import hash_snapshot
from quantlab.monitoring.models import EquityPoint, PerformanceSnapshot, PnLBreakdown
from quantlab.paper_oms.models import PaperAccount


def snapshot_from_account(
    account: PaperAccount,
    pnl: PnLBreakdown,
    *,
    as_of: datetime,
    snapshot_id: str,
) -> PerformanceSnapshot:
    equity = EquityPoint(
        as_of=as_of,
        cash=account.cash,
        reserved_cash=account.reserved_cash,
        market_value=account.market_value,
        equity=account.equity,
        note="Paper mark. Not a broker NAV.",
    )
    snap = PerformanceSnapshot(
        snapshot_id=snapshot_id,
        as_of=as_of,
        equity=equity,
        pnl=pnl,
    )
    return snap.model_copy(update={"snapshot_hash": hash_snapshot(snap)})
