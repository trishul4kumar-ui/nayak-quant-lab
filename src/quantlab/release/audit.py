"""Append-only certification audit."""

from __future__ import annotations

from threading import Lock

from quantlab.release.models import CertificationResult

_LOCK = Lock()
_LOG: list[CertificationResult] = []


def reset_for_tests() -> None:
    with _LOCK:
        _LOG.clear()


def record(result: CertificationResult) -> None:
    with _LOCK:
        _LOG.append(result)


def history() -> list[CertificationResult]:
    with _LOCK:
        return list(_LOG)
