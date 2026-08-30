"""In-memory real-time snapshot store. Snapshots are immutable."""

from __future__ import annotations

from threading import Lock

from quantlab.realtime_data.errors import RealTimeDataError
from quantlab.realtime_data.models import RealTimeSnapshot

_LOCK = Lock()
_ITEMS: dict[str, RealTimeSnapshot] = {}
_ORDER: list[str] = []


def reset_for_tests() -> None:
    with _LOCK:
        _ITEMS.clear()
        _ORDER.clear()


def put(snapshot: RealTimeSnapshot) -> RealTimeSnapshot:
    with _LOCK:
        if snapshot.snapshot_id in _ITEMS:
            existing = _ITEMS[snapshot.snapshot_id]
            if existing.snapshot_hash != snapshot.snapshot_hash:
                raise RealTimeDataError("snapshot identity collision")
            return existing
        _ITEMS[snapshot.snapshot_id] = snapshot
        _ORDER.append(snapshot.snapshot_id)
        return snapshot


def get(snapshot_id: str) -> RealTimeSnapshot | None:
    with _LOCK:
        if snapshot_id == "last":
            if not _ORDER:
                return None
            return _ITEMS[_ORDER[-1]]
        return _ITEMS.get(snapshot_id)


def list_ids() -> list[str]:
    with _LOCK:
        return list(_ORDER)
