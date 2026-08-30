"""In-process certification store."""

from __future__ import annotations

from threading import Lock

from quantlab.certification.models import CertificationResult

_LOCK = Lock()
_RESULTS: dict[str, CertificationResult] = {}
_BY_CANDIDATE: dict[str, str] = {}
_BY_KEY: dict[str, str] = {}
_LAST: str | None = None


def put_result(result: CertificationResult, *, key: str) -> CertificationResult:
    global _LAST
    with _LOCK:
        run_id = result.run.certification_id
        _RESULTS[run_id] = result
        _BY_CANDIDATE[result.candidate.candidate_id] = run_id
        _BY_KEY[key] = run_id
        _LAST = run_id
        return result


def get_result(run_id: str) -> CertificationResult | None:
    if run_id in _RESULTS:
        return _RESULTS[run_id]
    if run_id in _BY_CANDIDATE:
        return _RESULTS.get(_BY_CANDIDATE[run_id])
    if run_id in {"", "last"} and _LAST is not None:
        return _RESULTS.get(_LAST)
    prefix = [item for item in _RESULTS if item.startswith(run_id)]
    if len(prefix) == 1:
        return _RESULTS[prefix[0]]
    return None


def last_result() -> CertificationResult | None:
    if _LAST is None:
        return None
    return _RESULTS.get(_LAST)


def list_runs() -> list[CertificationResult]:
    return list(_RESULTS.values())


def lookup(key: str) -> CertificationResult | None:
    run_id = _BY_KEY.get(key)
    if run_id is None:
        return None
    return _RESULTS.get(run_id)


def reset() -> None:
    global _LAST
    with _LOCK:
        _RESULTS.clear()
        _BY_CANDIDATE.clear()
        _BY_KEY.clear()
        _LAST = None
