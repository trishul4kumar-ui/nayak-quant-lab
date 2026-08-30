"""Shadow portfolio is labelled SHADOW_POSITION. Never a brokerage book."""

from __future__ import annotations

from quantlab.paper_oms.models import PaperAccount
from quantlab.shadow.enums import PositionBook
from quantlab.shadow.models import ShadowPortfolio, ShadowPosition


def from_paper_account(account: PaperAccount, *, account_id: str) -> ShadowPortfolio:
    positions = {
        name: ShadowPosition(
            security_id=name,
            quantity=pos.quantity,
            market_price=pos.market_price,
            market_value=pos.market_value,
            book=PositionBook.SHADOW_POSITION,
        )
        for name, pos in account.positions.items()
    }
    equity = account.cash + account.market_value
    return ShadowPortfolio(
        account_id=account_id,
        book=PositionBook.SHADOW_POSITION,
        cash=account.cash,
        market_value=account.market_value,
        equity=equity,
        realized_pnl=account.realized_pnl,
        unrealized_pnl=account.unrealized_pnl,
        fees=account.fees,
        turnover=account.turnover,
        positions=positions,
        note="SHADOW_POSITION book. Not PAPER_POSITION. Not BROKER_POSITION.",
    )
