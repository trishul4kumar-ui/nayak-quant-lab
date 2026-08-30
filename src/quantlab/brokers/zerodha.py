from quantlab.core.errors import SafetyError
from quantlab.domain.models import Order


class ZerodhaGateway:
    """Placeholder. Live Zerodha is Phase 10 and never imported by strategies."""

    def place_order(self, order: Order) -> Order:
        raise SafetyError("Zerodha adapter is disabled until Phase 10")
