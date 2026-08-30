"""In-process ops results."""

from __future__ import annotations

from threading import Lock

from quantlab.ops.models import OpsResult

_LOCK = Lock()
_RESULTS: dict[str, OpsResult] = {}
_LAST: str | None = None


def reset_for_tests() -> None:
    global _LAST
    with _LOCK:
        _RESULTS.clear()
        _LAST = None


def put(result: OpsResult) -> OpsResult:
    global _LAST
    with _LOCK:
        _RESULTS[result.run_id] = result
        _LAST = result.run_id
        return result


def last() -> OpsResult | None:
    if _LAST is None:
        return None
    return _RESULTS.get(_LAST)
