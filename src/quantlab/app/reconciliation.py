"""Application boundary for reconciliation reports. Qt only receives immutable payloads."""

from __future__ import annotations

from typing import Any

from quantlab.broker_gateway.service import last_snapshot, matching_internal_books, snapshot
from quantlab.reconciliation.repository import audit, exceptions, last
from quantlab.reconciliation.service import internal_from_books, reconcile

_LAST: dict[str, Any] | None = None


def run_payload() -> dict[str, Any]:
    broker = last_snapshot() or snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    report = reconcile(broker, internal)
    payload = report.model_dump(mode="json")
    global _LAST
    _LAST = payload
    return payload


def last_run_row() -> dict[str, Any] | None:
    return _LAST


def status_payload() -> dict[str, Any]:
    report = last()
    return {
        "status": report.status.value if report else "UNKNOWN",
        "exception_count": len(report.exceptions) if report else 0,
        "live_trading": False,
        "write_enabled": False,
    }


def exceptions_payload() -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in exceptions()]


def audit_payload() -> list[dict[str, str]]:
    return audit()
