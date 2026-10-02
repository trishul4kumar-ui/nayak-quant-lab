"""Append-only in-process production-shadow evidence store."""

from __future__ import annotations

from threading import Lock

from quantlab.production_shadow.models import ProductionShadowRun

_LOCK = Lock()
_RUNS: dict[str, ProductionShadowRun] = {}
_ORDER: list[str] = []
_STATE = "STOPPED"
_AUDIT: list[dict[str, str]] = []


def reset_for_tests() -> None:
    global _STATE
    with _LOCK:
        _RUNS.clear()
        _ORDER.clear()
        _AUDIT.clear()
        _STATE = "STOPPED"


def put(run: ProductionShadowRun) -> ProductionShadowRun:
    with _LOCK:
        existing = _RUNS.get(run.shadow_run_id)
        if existing is not None and existing.run_hash != run.run_hash:
            raise ValueError("production-shadow identity collision")
        if existing is not None:
            return existing
        _RUNS[run.shadow_run_id] = run
        _ORDER.append(run.shadow_run_id)
        _AUDIT.append({"event": "shadow_assessed", "run_id": run.shadow_run_id})
        return run


def last() -> ProductionShadowRun | None:
    with _LOCK:
        return _RUNS[_ORDER[-1]] if _ORDER else None


def history() -> list[ProductionShadowRun]:
    with _LOCK:
        return [_RUNS[item] for item in _ORDER]


def set_state(value: str) -> str:
    global _STATE
    with _LOCK:
        _STATE = value
        _AUDIT.append({"event": "state", "value": value})
        return _STATE


def state() -> str:
    with _LOCK:
        return _STATE


def audit() -> list[dict[str, str]]:
    with _LOCK:
        return list(_AUDIT)
