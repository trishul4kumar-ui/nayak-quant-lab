"""Validated research-status transitions. The UI cannot invent a status."""

from __future__ import annotations

from quantlab.orchestration.contracts import ALLOWED_TRANSITIONS, ResearchStatus
from quantlab.orchestration.errors import OrchestrationError


def can_transition(current: ResearchStatus, nxt: ResearchStatus) -> bool:
    if current is nxt:
        return True
    return nxt in ALLOWED_TRANSITIONS.get(current, frozenset())


def transition(current: ResearchStatus, nxt: ResearchStatus) -> ResearchStatus:
    if not can_transition(current, nxt):
        raise OrchestrationError(f"illegal status transition {current.value} -> {nxt.value}")
    return nxt
