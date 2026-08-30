"""In-process supervisor of logical services. Crash-loop is contained."""

from __future__ import annotations

from threading import Lock

from quantlab.ops.lifecycle import crash, restart
from quantlab.ops.models import LogicalProcess, ProcessStatus
from quantlab.ops.process import SERVICES, spawn

_LOCK = Lock()
_PROCS: dict[str, LogicalProcess] = {}
_STARTED_CYCLES: set[str] = set()


def reset_for_tests() -> None:
    with _LOCK:
        _PROCS.clear()
        _STARTED_CYCLES.clear()
        for name in SERVICES:
            _PROCS[name] = spawn(name)


reset_for_tests()


def processes() -> dict[str, LogicalProcess]:
    with _LOCK:
        return dict(_PROCS)


def start(name: str) -> LogicalProcess:
    with _LOCK:
        current = _PROCS[name]
        if current.status is ProcessStatus.RUNNING:
            return current
        started = spawn(name)
        _PROCS[name] = started
        return started


def stop(name: str) -> LogicalProcess:
    with _LOCK:
        current = _PROCS[name]
        stopped = current.model_copy(update={"status": ProcessStatus.STOPPED})
        _PROCS[name] = stopped
        return stopped


def fail(name: str, *, error: str) -> LogicalProcess:
    with _LOCK:
        current = crash(_PROCS[name], error=error)
        _PROCS[name] = current
        return current


def restart_one(name: str) -> LogicalProcess:
    with _LOCK:
        current = restart(_PROCS[name])
        _PROCS[name] = current
        return current


def mark_cycle(cycle_id: str) -> bool:
    """Return True if this paper/shadow cycle is new (no duplicate restart run)."""
    with _LOCK:
        if cycle_id in _STARTED_CYCLES:
            return False
        _STARTED_CYCLES.add(cycle_id)
        return True
