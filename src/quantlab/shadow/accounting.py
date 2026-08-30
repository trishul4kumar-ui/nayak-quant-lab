"""Paper accounting remains Prompt 18. Shadow only checks identity."""

from __future__ import annotations

from quantlab.paper_oms.models import PaperAccount
from quantlab.shadow.models import ShadowPortfolio


def cash_identity(account: PaperAccount, portfolio: ShadowPortfolio, *, tol: float = 1e-6) -> bool:
    return abs(account.cash - portfolio.cash) <= tol


def equity_identity(
    account: PaperAccount, portfolio: ShadowPortfolio, *, tol: float = 1e-6
) -> bool:
    expected = portfolio.cash + portfolio.market_value
    return abs(portfolio.equity - expected) <= tol and abs(account.equity - expected) <= tol
