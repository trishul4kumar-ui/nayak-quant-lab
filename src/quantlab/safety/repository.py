"""In-process safety evaluations. Restart loses RAM; ledger is durable."""

from __future__ import annotations

from threading import Lock

from quantlab.safety.models import SafetyResult

_LOCK = Lock()
_RESULTS: dict[str, SafetyResult] = {}
_LAST: str | None = None


def reset_for_tests() -> None:
    global _LAST
    with _LOCK:
        _RESULTS.clear()
        _LAST = None


def put(result: SafetyResult) -> SafetyResult:
    global _LAST
    with _LOCK:
        _RESULTS[result.evaluation_id] = result
        _LAST = result.evaluation_id
        return result


def get(evaluation_id: str) -> SafetyResult | None:
    if evaluation_id in {"", "last"}:
        return last()
    return _RESULTS.get(evaluation_id)


def last() -> SafetyResult | None:
    if _LAST is None:
        return None
    return _RESULTS.get(_LAST)


def list_results() -> list[SafetyResult]:
    return list(_RESULTS.values())
