"""Re-export discovery errors. Package must not own a second error hierarchy."""

from quantlab.core.errors import DiscoveryError

__all__ = ["DiscoveryError"]
