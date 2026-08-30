"""Position marks. Shorting is allowed only when the paper account permits it."""

from __future__ import annotations

from datetime import datetime

from quantlab.paper_oms.models import PaperAccount, PaperMarketSnapshot, PaperPosition


def mark_positions(account: PaperAccount, snapshot: PaperMarketSnapshot) -> PaperAccount:
    positions: dict[str, PaperPosition] = {}
    market_value = 0.0
    unrealized = 0.0
    realized = 0.0
    for name, position in account.positions.items():
        price = snapshot.prices.get(name, position.market_price)
        qty = position.quantity
        mv = qty * price
        upnl = qty * (price - position.average_cost)
        marked = position.model_copy(
            update={
                "market_price": price,
                "market_value": mv,
                "unrealized_pnl": upnl,
                "gross_exposure": abs(mv),
                "last_update": snapshot.as_of,
            }
        )
        positions[name] = marked
        market_value += mv
        unrealized += upnl
        realized += marked.realized_pnl
    equity = account.cash + market_value
    for name, position in positions.items():
        weight = (position.market_value / equity) if equity else 0.0
        positions[name] = position.model_copy(update={"weight": weight})
    gross = sum(abs(item.market_value) for item in positions.values())
    net = sum(item.market_value for item in positions.values())
    return account.model_copy(
        update={
            "positions": positions,
            "market_value": market_value,
            "equity": equity,
            "available_cash": account.cash - account.reserved_cash,
            "gross_exposure": gross / equity if equity else 0.0,
            "net_exposure": net / equity if equity else 0.0,
            "unrealized_pnl": unrealized,
            "realized_pnl": realized,
        }
    )


def upsert_position(
    positions: dict[str, PaperPosition],
    security_id: str,
    *,
    quantity: float,
    average_cost: float,
    realized_pnl: float,
    price: float,
    as_of: datetime,
) -> dict[str, PaperPosition]:
    updated = dict(positions)
    if abs(quantity) <= 1e-12:
        updated.pop(security_id, None)
        return updated
    mv = quantity * price
    updated[security_id] = PaperPosition(
        security_id=security_id,
        quantity=quantity,
        average_cost=average_cost,
        market_price=price,
        market_value=mv,
        realized_pnl=realized_pnl,
        unrealized_pnl=quantity * (price - average_cost),
        gross_exposure=abs(mv),
        last_update=as_of,
    )
    return updated
