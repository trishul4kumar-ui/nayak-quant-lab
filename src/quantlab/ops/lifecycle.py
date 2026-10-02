"""Process lifecycle helpers. Restarts are bounded."""

from __future__ import annotations

from quantlab.ops.models import LogicalProcess, ProcessStatus, RestartPolicy
from quantlab.ops.process import identity


def crash(process: LogicalProcess, *, error: str) -> LogicalProcess:
    return process.model_copy(update={"status": ProcessStatus.FAILED, "last_error": error})


def restart(process: LogicalProcess) -> LogicalProcess:
    if process.restart_policy is RestartPolicy.NEVER:
        return process.model_copy(update={"status": ProcessStatus.HALTED})
    if process.restart_policy is RestartPolicy.MANUAL:
        return process.model_copy(update={"status": ProcessStatus.STOPPED})
    nxt = process.restarts + 1
    if process.restart_policy is RestartPolicy.LIMITED_RESTARTS and nxt > process.max_restarts:
        return process.model_copy(update={"status": ProcessStatus.CRASH_LOOP, "restarts": nxt})
    generation = nxt
    return process.model_copy(
        update={
            "status": ProcessStatus.RUNNING,
            "restarts": nxt,
            "identity": identity(process.name, generation),
            "last_error": "",
        }
    )
