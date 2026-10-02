"""Restricted execution gateway.

This package is intentionally unable to construct strategy decisions or enable a
production broker adapter.  It only evaluates a pre-existing, hash-bound order
envelope and fails closed by default.
"""

from quantlab.restricted_execution.service import RestrictedExecutionGateway

__all__ = ["RestrictedExecutionGateway"]
