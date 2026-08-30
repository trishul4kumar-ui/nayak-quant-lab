from quantlab.core.errors import SafetyError
from quantlab.domain.models import Order, PortfolioState, Position


class ReconciliationReport:
    def __init__(self, matched: bool, mismatches: list[str]) -> None:
        self.matched = matched
        self.mismatches = mismatches

    def allows_live_orders(self) -> bool:
        return self.matched


class ReconciliationEngine:
    """If QUANT LAB and broker disagree, no new live orders."""

    def compare(
        self,
        internal: PortfolioState,
        broker_cash: float,
        broker_positions: list[Position],
        open_orders: list[Order],
    ) -> ReconciliationReport:
        mismatches: list[str] = []
        if abs(internal.cash - broker_cash) > 1e-6:
            mismatches.append("cash")
        internal_map = {str(p.instrument): p.quantity for p in internal.positions}
        broker_map = {str(p.instrument): p.quantity for p in broker_positions}
        if internal_map != broker_map:
            mismatches.append("positions")
        if open_orders:
            mismatches.append("open_orders_unreconciled")
        return ReconciliationReport(matched=not mismatches, mismatches=mismatches)

    def require_live_clearance(self, report: ReconciliationReport) -> None:
        if not report.allows_live_orders():
            raise SafetyError("reconciliation failed: " + ",".join(report.mismatches))
