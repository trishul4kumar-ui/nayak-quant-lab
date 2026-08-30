"""In-memory twin runs. Events are append-only."""

from __future__ import annotations

from threading import Lock

from quantlab.digital_twin.errors import DigitalTwinError
from quantlab.digital_twin.models import TwinRun

_LOCK = Lock()
_ITEMS: dict[str, TwinRun] = {}
_ORDER: list[str] = []


def reset_for_tests() -> None:
    with _LOCK:
        _ITEMS.clear()
        _ORDER.clear()


def put(item: TwinRun) -> TwinRun:
    with _LOCK:
        if item.run_id in _ITEMS:
            existing = _ITEMS[item.run_id]
            if existing.state_hash != item.state_hash:
                raise DigitalTwinError("twin run identity collision")
            return existing
        _ITEMS[item.run_id] = item
        _ORDER.append(item.run_id)
        return item


def get(run_id: str) -> TwinRun | None:
    with _LOCK:
        if run_id == "last":
            if not _ORDER:
                return None
            return _ITEMS[_ORDER[-1]]
        return _ITEMS.get(run_id)


def list_ids() -> list[str]:
    with _LOCK:
        return list(_ORDER)


def replace(item: TwinRun) -> TwinRun:
    """Replace is only allowed when identity is unchanged; used for halt labels."""
    with _LOCK:
        _ITEMS[item.run_id] = item
        if item.run_id not in _ORDER:
            _ORDER.append(item.run_id)
        return item
