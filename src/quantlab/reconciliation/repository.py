"""Append-only in-memory reconciliation evidence store."""

from __future__ import annotations

from threading import Lock

from quantlab.reconciliation.models import ReconciliationException, ReconciliationReport

_LOCK = Lock()
_REPORTS: dict[str, ReconciliationReport] = {}
_ORDER: list[str] = []
_EXCEPTIONS: dict[str, ReconciliationException] = {}
_AUDIT: list[dict[str, str]] = []


def reset_for_tests() -> None:
    with _LOCK:
        _REPORTS.clear()
        _ORDER.clear()
        _EXCEPTIONS.clear()
        _AUDIT.clear()


def put(report: ReconciliationReport) -> ReconciliationReport:
    with _LOCK:
        existing = _REPORTS.get(report.reconciliation_id)
        if existing is not None and existing.reconciliation_hash != report.reconciliation_hash:
            raise ValueError("reconciliation identity collision")
        if existing is not None:
            return existing
        _REPORTS[report.reconciliation_id] = report
        _ORDER.append(report.reconciliation_id)
        for item in report.exceptions:
            _EXCEPTIONS.setdefault(item.exception_id, item)
        _AUDIT.append({"event": "report_created", "report_id": report.reconciliation_id})
        return report


def last() -> ReconciliationReport | None:
    with _LOCK:
        return _REPORTS[_ORDER[-1]] if _ORDER else None


def get(report_id: str) -> ReconciliationReport | None:
    with _LOCK:
        return last() if report_id in {"", "last"} else _REPORTS.get(report_id)


def history() -> list[ReconciliationReport]:
    with _LOCK:
        return [_REPORTS[item] for item in _ORDER]


def exceptions() -> list[ReconciliationException]:
    with _LOCK:
        return list(_EXCEPTIONS.values())


def update_exception(item: ReconciliationException) -> ReconciliationException:
    with _LOCK:
        existing = _EXCEPTIONS.get(item.exception_id)
        if existing is None:
            raise KeyError(item.exception_id)
        if item.created_at != existing.created_at or item.dimension != existing.dimension:
            raise ValueError("reconciliation discrepancy evidence is immutable")
        _EXCEPTIONS[item.exception_id] = item
        _AUDIT.append({"event": "exception_transition", "exception_id": item.exception_id})
        return item


def audit() -> list[dict[str, str]]:
    with _LOCK:
        return list(_AUDIT)
