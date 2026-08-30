"""Re-export gateway errors. Package must not own a second error hierarchy."""

from quantlab.core.errors import (
    AuthorizationError,
    GatewayError,
    InvalidSafetyTransition,
    KillSwitchError,
    ReleaseBlocked,
    SafetyError,
)

__all__ = [
    "AuthorizationError",
    "GatewayError",
    "InvalidSafetyTransition",
    "KillSwitchError",
    "ReleaseBlocked",
    "SafetyError",
]
