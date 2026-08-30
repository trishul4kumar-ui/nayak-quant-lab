"""In-process shadow engine state. Restart uses the JSON checkpoint sidecar."""

from __future__ import annotations

from threading import Lock

from quantlab.shadow.enums import KillReason, ShadowMode
from quantlab.shadow.models import Heartbeat, ShadowIncident, ShadowResult

_LOCK = Lock()
_RESULTS: dict[str, ShadowResult] = {}
_BY_KEY: dict[str, str] = {}
_LAST: str | None = None
_MODE: ShadowMode = ShadowMode.OFF
_KILL: KillReason | None = None
_INCIDENTS: list[ShadowIncident] = []
_HEARTBEAT = Heartbeat()


def mode() -> ShadowMode:
    return _MODE


def set_mode(value: ShadowMode) -> ShadowMode:
    global _MODE
    with _LOCK:
        _MODE = value
        return _MODE


def kill_reason() -> KillReason | None:
    return _KILL


def set_kill(reason: KillReason | None) -> None:
    global _KILL
    with _LOCK:
        _KILL = reason
        if reason is not None:
            _MODE = ShadowMode.HALTED


def put_result(result: ShadowResult, *, key: str) -> ShadowResult:
    global _LAST, _HEARTBEAT
    with _LOCK:
        existing = _BY_KEY.get(key)
        if existing is not None and existing in _RESULTS:
            return _RESULTS[existing]
        cycle_id = result.cycle.cycle_id
        _RESULTS[cycle_id] = result
        _BY_KEY[key] = cycle_id
        _LAST = cycle_id
        success = cycle_id if result.cycle.status.value == "completed" else _HEARTBEAT.last_success
        _HEARTBEAT = Heartbeat(
            last_cycle=cycle_id,
            last_success=success,
            last_data=result.freshness.data_timestamp.isoformat(),
            last_reconciliation=result.reconciliation.status,
            last_checkpoint=result.checkpoint.checkpoint_id if result.checkpoint else "",
            last_health_check=_HEARTBEAT.last_health_check,
            idle=False,
            dead=False,
        )
        return result


def lookup(key: str) -> ShadowResult | None:
    cycle_id = _BY_KEY.get(key)
    if cycle_id is None:
        return None
    return _RESULTS.get(cycle_id)


def get_result(cycle_id: str) -> ShadowResult | None:
    if cycle_id in _RESULTS:
        return _RESULTS[cycle_id]
    if cycle_id in {"", "last"} and _LAST is not None:
        return _RESULTS.get(_LAST)
    prefix = [item for item in _RESULTS if item.startswith(cycle_id)]
    if len(prefix) == 1:
        return _RESULTS[prefix[0]]
    return None


def last_result() -> ShadowResult | None:
    if _LAST is None:
        return None
    return _RESULTS.get(_LAST)


def list_results() -> list[ShadowResult]:
    return list(_RESULTS.values())


def add_incident(item: ShadowIncident) -> ShadowIncident:
    with _LOCK:
        _INCIDENTS.append(item)
        return item


def list_incidents() -> list[ShadowIncident]:
    return list(_INCIDENTS)


def heartbeat() -> Heartbeat:
    return _HEARTBEAT


def touch_health(stamp: str) -> Heartbeat:
    global _HEARTBEAT
    with _LOCK:
        _HEARTBEAT = _HEARTBEAT.model_copy(update={"last_health_check": stamp, "idle": True})
        return _HEARTBEAT


def reset() -> None:
    global _LAST, _MODE, _KILL, _HEARTBEAT
    with _LOCK:
        _RESULTS.clear()
        _BY_KEY.clear()
        _INCIDENTS.clear()
        _LAST = None
        _MODE = ShadowMode.OFF
        _KILL = None
        _HEARTBEAT = Heartbeat()
