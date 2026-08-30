"""Explicit safety transitions. Illegal paths raise InvalidSafetyTransition."""

from quantlab.safety.state import LEGAL, SafetyState, transition

__all__ = ["LEGAL", "SafetyState", "transition"]
