from quantlab.core.errors import SafetyError
from quantlab.domain.models import Order, OrderStatus, Position


class PaperGateway:
    """Records intended orders. Never talks to a real broker."""

    name = "paper"

    def __init__(self) -> None:
        self.orders: list[Order] = []
        self.positions: list[Position] = []
        self.cash = 1_000_000.0

    def get_account(self) -> dict[str, float]:
        return {"cash": self.cash}

    def get_positions(self) -> list[Position]:
        return list(self.positions)

    def get_orders(self) -> list[Order]:
        return list(self.orders)

    def place_order(self, order: Order) -> Order:
        order.status = OrderStatus.ACKNOWLEDGED
        self.orders.append(order)
        return order

    def cancel_order(self, order_id: str) -> Order:
        for order in self.orders:
            if order.id == order_id:
                order.status = OrderStatus.CANCELLED
                return order
        raise SafetyError(f"unknown paper order {order_id}")


class OpenAlgoGateway:
    """Placeholder. Implemented only after paper + reconcile pass."""

    def place_order(self, order: Order) -> Order:
        raise SafetyError("OpenAlgo adapter is disabled until Phase 8")
