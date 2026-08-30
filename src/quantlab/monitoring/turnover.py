"""Turnover from paper fills. Diagnostic, not a rebalance."""

from __future__ import annotations

from quantlab.paper_oms.models import PaperFill


def fill_turnover(fills: list[PaperFill], *, equity: float) -> float:
    if equity <= 0:
        return 0.0
    traded = sum(abs(item.gross_notional) for item in fills)
    return traded / equity
