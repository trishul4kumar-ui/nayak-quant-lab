"""Ops domain types. Operations ≠ strategy ≠ broker."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from quantlab.ops.state import OpsState


class EnvironmentName(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    RESEARCH = "research"
    PAPER = "paper"
    SHADOW = "shadow"
    PRODUCTION = "production"


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"
    HALTED = "halted"
    RECOVERY = "recovery"
    UNKNOWN = "unknown"


class RestartPolicy(StrEnum):
    NEVER = "never"
    ON_FAILURE = "on_failure"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LIMITED_RESTARTS = "limited_restarts"
    MANUAL = "manual"


class ProcessStatus(StrEnum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    HALTED = "halted"
    CRASH_LOOP = "crash_loop"


class SecretReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    version: str = "1"
    expires_at: datetime | None = None
    present: bool = False
    note: str = "Reference only. Value is never logged."


class SecretMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    version: str
    expired: bool = False


class SecretAccessAudit(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    actor: str
    timestamp: datetime
    purpose: str
    leaked: bool = False


class LogicalProcess(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    status: ProcessStatus = ProcessStatus.STOPPED
    restart_policy: RestartPolicy = RestartPolicy.LIMITED_RESTARTS
    restarts: int = 0
    max_restarts: int = 3
    identity: str = ""
    last_error: str = ""


class OpsIncident(BaseModel):
    model_config = ConfigDict(frozen=True)

    incident_id: str
    kind: str
    detail: str
    timestamp: datetime


class BackupRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    backup_id: str
    path: str
    checksum: str
    verified: bool = False
    created_at: datetime
    recovery_ready: bool = False


class ReleaseIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    software_version: str
    config_hash: str
    environment: EnvironmentName
    timestamp: datetime
    note: str = "Release identity is not live authorization."


class OpsResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    state: OpsState
    health: HealthStatus
    readiness: bool
    live_trading: bool = False
    config_hash: str = ""
    environment: EnvironmentName = EnvironmentName.RESEARCH
    processes: tuple[LogicalProcess, ...] = ()
    incidents: tuple[OpsIncident, ...] = ()
    extras: dict[str, Any] = Field(default_factory=dict)
    result_hash: str = ""
    note: str = "Ops control plane. LIVE_TRADING=false."
