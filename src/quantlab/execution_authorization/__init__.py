"""Restricted-live eligibility assessment. It never sends or changes broker orders."""

from quantlab.execution_authorization.service import approve, assess, revoke

__all__ = ["approve", "assess", "revoke"]
