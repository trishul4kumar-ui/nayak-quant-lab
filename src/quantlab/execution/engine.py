from __future__ import annotations

from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import SafetyError
from quantlab.domain.models import Order, OrderStatus


class ExecutionEngine:
    """OMS façade. Live placement is impossible unless every safety gate passes."""

    def __init__(self, gates: LiveSafetyGates | None = None) -> None:
        self.gates = gates or LiveSafetyGates()

    def submit(self, order: Order, live: bool = False) -> Order:
        if live:
            if not self.gates.all_pass():
                raise SafetyError("live submit blocked: " + ",".join(self.gates.blocking_reasons()))
            raise SafetyError("live broker path is not implemented")
        if order.status == OrderStatus.CREATED:
            order.status = OrderStatus.VALIDATING
        return order
