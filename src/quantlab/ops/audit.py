"""Audit writer. Failure affects readiness. Shutdown must flush."""

from __future__ import annotations

from threading import Lock

from quantlab.ops.models import OpsResult

_LOCK = Lock()
_HEALTHY = True
_BUFFER: list[OpsResult] = []
_FLUSHED = False


def reset_for_tests() -> None:
    global _HEALTHY, _FLUSHED
    with _LOCK:
        _BUFFER.clear()
        _HEALTHY = True
        _FLUSHED = False


def writer_healthy() -> bool:
    return _HEALTHY


def mark_failure() -> None:
    global _HEALTHY
    _HEALTHY = False


def append(result: OpsResult) -> None:
    if not _HEALTHY:
        return
    with _LOCK:
        _BUFFER.append(result)


def flush() -> int:
    global _FLUSHED
    with _LOCK:
        count = len(_BUFFER)
        _FLUSHED = True
        return count


def flushed() -> bool:
    return _FLUSHED


def history() -> list[OpsResult]:
    with _LOCK:
        return list(_BUFFER)
