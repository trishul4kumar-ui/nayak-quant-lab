"""Remote-only, manually confirmed Kite execution boundary.

This package is deployed separately from the desktop application.  It deliberately
does not participate in research, signal generation, or portfolio construction.
"""

from quantlab.kite_execution_gateway.service import SecureKiteExecutionGateway

__all__ = ["SecureKiteExecutionGateway"]
