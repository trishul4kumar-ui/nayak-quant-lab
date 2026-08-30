"""Pre-submit paper validation. Failures are typed rejections, not silent clips."""

from __future__ import annotations

from quantlab.data.fabric.calendar import WeekdayCalendar
from quantlab.domain.models import Side
from quantlab.paper_oms.enums import PaperOrderType, TimeInForce
from quantlab.paper_oms.errors import (
    InsufficientCashError,
    InsufficientPositionError,
    OMSValidationError,
    UnsupportedOrderTypeError,
)
from quantlab.paper_oms.models import PaperAccount, PaperMarketSnapshot, PaperOrder
from quantlab.risk.firewall import RiskFirewall
from quantlab.risk.states import allows_new_exposure


def validate_order(
    order: PaperOrder,
    account: PaperAccount,
    snapshot: PaperMarketSnapshot,
    *,
    firewall: RiskFirewall | None = None,
) -> None:
    if order.rounded_quantity <= 0:
        raise OMSValidationError("quantity must be > 0")
    if order.security_id not in snapshot.prices:
        raise OMSValidationError(f"security {order.security_id} missing from PIT snapshot")
    if snapshot.tradable and not snapshot.tradable.get(order.security_id, True):
        raise OMSValidationError(f"instrument {order.security_id} is not tradable")
    if order.order_type is not PaperOrderType.MARKET:
        raise UnsupportedOrderTypeError(f"unsupported paper order type {order.order_type}")
    if order.time_in_force is not TimeInForce.DAY:
        raise OMSValidationError(f"unsupported time-in-force {order.time_in_force}")
    if order.reference_price <= 0:
        raise OMSValidationError("price must be positive")
    calendar = WeekdayCalendar()
    if not calendar.is_session(snapshot.as_of.date()):
        raise OMSValidationError(
            "as_of is not a weekday session (official NSE holidays NOT_TESTED)"
        )
    if order.side is Side.BUY:
        need = order.rounded_quantity * order.reference_price
        if account.available_cash + 1e-9 < need:
            raise InsufficientCashError("insufficient paper cash for buy")
        if firewall is not None and not allows_new_exposure(firewall.state):
            raise OMSValidationError(f"risk firewall {firewall.state.value} rejects new exposure")
    else:
        held = 0.0
        position = account.positions.get(order.security_id)
        if position is not None:
            held = position.quantity
        if held + 1e-9 < order.rounded_quantity and not account.allow_short:
            raise InsufficientPositionError("insufficient paper position for sell")
