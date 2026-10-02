"""Holdings concentration (HHI). Not a risk-limit change."""

from __future__ import annotations

from quantlab.paper_oms.models import PaperAccount


def herfindahl(account: PaperAccount) -> float:
    if account.equity == 0:
        return 0.0
    weights = [abs(pos.market_value) / account.equity for pos in account.positions.values()]
    return sum(w * w for w in weights)
