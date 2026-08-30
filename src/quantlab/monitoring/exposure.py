"""Gross/net/long/short exposure from paper books."""

from __future__ import annotations

from quantlab.paper_oms.models import PaperAccount


def exposure_map(account: PaperAccount) -> dict[str, float]:
    long_exp = sum(max(p.market_value, 0.0) for p in account.positions.values())
    short_exp = sum(min(p.market_value, 0.0) for p in account.positions.values())
    return {
        "gross": account.gross_exposure,
        "net": account.net_exposure,
        "long": long_exp,
        "short": abs(short_exp),
        "cash": account.cash,
        "reserved_cash": account.reserved_cash,
        "market_value": account.market_value,
        "equity": account.equity,
    }
