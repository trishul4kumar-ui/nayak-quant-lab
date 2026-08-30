"""Safety audit records on the existing JSONL ledger. Not a second ledger."""

from __future__ import annotations

from threading import Lock

from quantlab.safety.models import SafetyIncident, SafetyResult

_LOCK = Lock()
_LOG: list[SafetyResult] = []


def reset_for_tests() -> None:
    with _LOCK:
        _LOG.clear()


def record(result: SafetyResult) -> None:
    with _LOCK:
        _LOG.append(result)


def history() -> list[SafetyResult]:
    with _LOCK:
        return list(_LOG)


def incidents() -> list[SafetyIncident]:
    rows: list[SafetyIncident] = []
    for item in history():
        rows.extend(item.incidents)
    return rows
