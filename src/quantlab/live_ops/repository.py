"""Append-only in-process operational record store for a local-first workspace."""

from __future__ import annotations

from threading import Lock

from quantlab.live_ops.models import AlertEvent, Incident, OperationalSnapshot, ResponseAction

_LOCK = Lock()
_ALERTS: dict[str, AlertEvent] = {}
_INCIDENTS: dict[str, Incident] = {}
_ACTIONS: dict[str, ResponseAction] = {}
_SNAPSHOTS: list[OperationalSnapshot] = []


def reset_for_tests() -> None:
    with _LOCK:
        _ALERTS.clear()
        _INCIDENTS.clear()
        _ACTIONS.clear()
        _SNAPSHOTS.clear()


def put_alert(item: AlertEvent) -> AlertEvent:
    with _LOCK:
        _ALERTS[item.fingerprint] = item
        return item


def alert(fingerprint: str) -> AlertEvent | None:
    with _LOCK:
        return _ALERTS.get(fingerprint)


def alerts() -> list[AlertEvent]:
    with _LOCK:
        return list(_ALERTS.values())


def put_incident(item: Incident) -> Incident:
    with _LOCK:
        _INCIDENTS[item.fingerprint] = item
        return item


def incident(fingerprint: str) -> Incident | None:
    with _LOCK:
        return _INCIDENTS.get(fingerprint)


def incident_by_id(incident_id: str) -> Incident | None:
    with _LOCK:
        return next((item for item in _INCIDENTS.values() if item.incident_id == incident_id), None)


def incidents() -> list[Incident]:
    with _LOCK:
        return list(_INCIDENTS.values())


def put_action(item: ResponseAction) -> ResponseAction:
    with _LOCK:
        prior = _ACTIONS.get(item.idempotency_key)
        if prior is not None:
            return prior
        _ACTIONS[item.idempotency_key] = item
        return item


def actions() -> list[ResponseAction]:
    with _LOCK:
        return list(_ACTIONS.values())


def put_snapshot(item: OperationalSnapshot) -> OperationalSnapshot:
    with _LOCK:
        _SNAPSHOTS.append(item)
        return item


def last_snapshot() -> OperationalSnapshot | None:
    with _LOCK:
        return _SNAPSHOTS[-1] if _SNAPSHOTS else None
