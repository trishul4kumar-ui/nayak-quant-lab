"""Re-export capital errors. Package must not own a second error hierarchy."""

from quantlab.core.errors import CapitalError, InfeasibleCapitalAllocation

__all__ = ["CapitalError", "InfeasibleCapitalAllocation"]
