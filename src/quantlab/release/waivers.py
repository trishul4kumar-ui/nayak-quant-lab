"""Controlled waivers. Safety cannot be waived. AI cannot approve."""

from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock

from quantlab.release.errors import ReleaseWaiverError
from quantlab.release.models import ActorKind, WaiverRecord

_LOCK = Lock()
_ITEMS: dict[str, WaiverRecord] = {}
_SAFETY = frozenset({"safety_readiness", "live_enablement"})


def reset_for_tests() -> None:
    with _LOCK:
        _ITEMS.clear()


def record(item: WaiverRecord, *, as_of: datetime | None = None) -> WaiverRecord:
    if item.actor is ActorKind.AI_SUGGESTION:
        raise ReleaseWaiverError("AI cannot create or approve waivers")
    if item.criterion_id in _SAFETY:
        raise ReleaseWaiverError("safety requirements cannot be waived")
    now = as_of or datetime(2024, 1, 2, tzinfo=UTC)
    if item.expires_at <= now:
        raise ReleaseWaiverError("waiver expired")
    with _LOCK:
        _ITEMS[item.waiver_id] = item
    return item


def list_waivers() -> list[WaiverRecord]:
    with _LOCK:
        return list(_ITEMS.values())
