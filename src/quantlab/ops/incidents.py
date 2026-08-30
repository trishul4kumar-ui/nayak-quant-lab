"""Ops incidents. Failures are retained."""

from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock

from quantlab.ops.models import OpsIncident

_LOCK = Lock()
_ITEMS: list[OpsIncident] = []


def reset_for_tests() -> None:
    with _LOCK:
        _ITEMS.clear()


def record(*, kind: str, detail: str) -> OpsIncident:
    item = OpsIncident(
        incident_id=f"ops-{len(_ITEMS) + 1}",
        kind=kind,
        detail=detail,
        timestamp=datetime(2024, 1, 2, tzinfo=UTC),
    )
    with _LOCK:
        _ITEMS.append(item)
    return item


def list_incidents() -> list[OpsIncident]:
    with _LOCK:
        return list(_ITEMS)
