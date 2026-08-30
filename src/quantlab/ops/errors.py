"""Re-export ops errors. Package must not own a second error hierarchy."""

from quantlab.core.errors import (
    BackupError,
    ClockError,
    InvalidOpsTransition,
    OpsError,
    SecretExposureError,
)

__all__ = [
    "BackupError",
    "ClockError",
    "InvalidOpsTransition",
    "OpsError",
    "SecretExposureError",
]
