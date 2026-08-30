"""In-process certification evaluations."""

from __future__ import annotations

from threading import Lock

from quantlab.release.models import CertificationResult

_LOCK = Lock()
_RESULTS: dict[str, CertificationResult] = {}
_LAST: str | None = None


def reset_for_tests() -> None:
    global _LAST
    with _LOCK:
        _RESULTS.clear()
        _LAST = None


def put(result: CertificationResult) -> CertificationResult:
    global _LAST
    with _LOCK:
        _RESULTS[result.evaluation_id] = result
        _LAST = result.evaluation_id
        return result


def get(evaluation_id: str) -> CertificationResult | None:
    if evaluation_id in {"", "last"}:
        return last()
    return _RESULTS.get(evaluation_id)


def last() -> CertificationResult | None:
    if _LAST is None:
        return None
    return _RESULTS.get(_LAST)


def list_results() -> list[CertificationResult]:
    return list(_RESULTS.values())
