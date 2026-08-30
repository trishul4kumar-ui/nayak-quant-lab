"""Logical process records. Not OS daemons. Identity is hashed."""

from __future__ import annotations

from quantlab.data.fabric.checksums import sha256_bytes
from quantlab.ops.models import LogicalProcess, ProcessStatus, RestartPolicy

SERVICES: tuple[str, ...] = (
    "app",
    "data",
    "research_jobs",
    "paper_oms",
    "monitoring",
    "shadow",
    "safety",
    "health",
    "scheduler",
    "audit_writer",
)


def identity(name: str, generation: int) -> str:
    return sha256_bytes(f"{name}|{generation}".encode())


def spawn(name: str, *, generation: int = 0) -> LogicalProcess:
    return LogicalProcess(
        name=name,
        status=ProcessStatus.RUNNING,
        restart_policy=RestartPolicy.LIMITED_RESTARTS,
        restarts=0,
        identity=identity(name, generation),
    )
