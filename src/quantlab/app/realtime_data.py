"""App-layer real-time data. Qt cannot parse streams or mutate snapshots."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from quantlab.core.errors import QuantLabError
from quantlab.realtime_data.service import (
    audit_history,
    health,
    inspect,
    list_snapshots,
    replay,
    snapshot,
    source_status,
    start,
    stop,
)
from quantlab.realtime_data.state import current

_LAST: dict[str, Any] | None = None


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _safe(fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return fn()
    except QuantLabError as exc:
        return {"error": str(exc), "live_trading": False, "observe_only": True}


def last_run_row() -> dict[str, Any] | None:
    return _LAST


def _store(row: dict[str, Any]) -> dict[str, Any]:
    global _LAST
    _LAST = row
    return row


def health_payload() -> dict[str, Any]:
    return _dump(health())


def status_payload() -> dict[str, Any]:
    item = health()
    return {
        "state": current().value,
        "overall": item.overall,
        "live_trading": False,
        "observe_only": True,
        "note": "CONNECTED ≠ HEALTHY. REAL-TIME OBSERVATION ≠ TRADING.",
    }


def sources_payload() -> dict[str, Any]:
    return {
        **source_status(),
        "write_enabled": False,
        "live_trading": False,
        "note": "Provider bridges are observe-only and must preserve provenance.",
    }


def start_payload(scenario: str = "normal", *, adapter: str | None = None) -> dict[str, Any]:
    return _safe(lambda: _dump(start(scenario, adapter_name=adapter)))


def stop_payload() -> dict[str, Any]:
    return _safe(lambda: _dump(stop()))


def snapshot_payload() -> dict[str, Any]:
    frozen = snapshot()
    return _store(
        {
            "id": frozen.snapshot_id,
            "hash": frozen.snapshot_hash,
            "quality": frozen.quality.value,
            "freshness": frozen.freshness.value,
            "session": frozen.session.value,
            "n_names": frozen.n_names,
            "live_trading": False,
            **_dump(frozen),
        }
    )


def inspect_payload(item_id: str = "last") -> dict[str, Any]:
    frozen = inspect(item_id) or snapshot()
    return _dump(frozen)


def quality_payload() -> dict[str, Any]:
    frozen = inspect("last") or snapshot()
    return {"quality": frozen.quality.value, "live_trading": False}


def freshness_payload() -> dict[str, Any]:
    frozen = inspect("last") or snapshot()
    return {"freshness": frozen.freshness.value, "live_trading": False}


def sequence_payload() -> dict[str, Any]:
    frozen = inspect("last") or snapshot()
    return {"sequence": frozen.sequence_kind.value, "live_trading": False}


def clock_payload() -> dict[str, Any]:
    return {"clock_health": health().clock_health, "live_trading": False}


def session_payload() -> dict[str, Any]:
    frozen = inspect("last") or snapshot()
    return {"session": frozen.session.value, "calendar_version": frozen.calendar_version}


def replay_payload() -> dict[str, Any]:
    return _safe(lambda: _dump(replay()))


def audit_payload() -> list[dict[str, Any]]:
    rows = audit_history()
    return rows or [{"note": "No realtime audit yet.", "live_trading": False}]


def list_payload() -> list[dict[str, Any]]:
    ids = list_snapshots()
    if not ids:
        return [{"note": "No snapshots.", "live_trading": False}]
    return [{"id": item, "live_trading": False} for item in ids]


def run_payload() -> dict[str, Any]:
    start()
    return snapshot_payload()
