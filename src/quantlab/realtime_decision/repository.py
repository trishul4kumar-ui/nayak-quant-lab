"""In-memory real-time decisions. Immutable after freeze."""

from __future__ import annotations

from threading import Lock

from quantlab.realtime_decision.errors import RealTimeDecisionError
from quantlab.realtime_decision.models import RealTimeDecision

_LOCK = Lock()
_ITEMS: dict[str, RealTimeDecision] = {}
_ORDER: list[str] = []


def reset_for_tests() -> None:
    with _LOCK:
        _ITEMS.clear()
        _ORDER.clear()


def put(item: RealTimeDecision) -> RealTimeDecision:
    with _LOCK:
        if item.decision_id in _ITEMS:
            existing = _ITEMS[item.decision_id]
            if existing.decision_hash != item.decision_hash:
                raise RealTimeDecisionError("decision identity collision")
            return existing
        _ITEMS[item.decision_id] = item
        _ORDER.append(item.decision_id)
        return item


def get(decision_id: str) -> RealTimeDecision | None:
    with _LOCK:
        if decision_id == "last":
            if not _ORDER:
                return None
            return _ITEMS[_ORDER[-1]]
        return _ITEMS.get(decision_id)


def list_ids() -> list[str]:
    with _LOCK:
        return list(_ORDER)
