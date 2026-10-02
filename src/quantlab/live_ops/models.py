"""Typed, audit-friendly operations contracts. They contain no trading decisions."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Severity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentState(StrEnum):
    DETECTED = "DETECTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INVESTIGATING = "INVESTIGATING"
    MITIGATED = "MITIGATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class ResponseActionKind(StrEnum):
    NOTIFY = "NOTIFY"
    PAUSE_SUBMISSIONS = "PAUSE_SUBMISSIONS"
    ACTIVATE_KILL_SWITCH = "ACTIVATE_KILL_SWITCH"
    HALT_SUBSYSTEM = "HALT_SUBSYSTEM"
    REQUEST_INVESTIGATION = "REQUEST_INVESTIGATION"


class HealthSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str
    component: str
    status: str
    observed_at: datetime
    evidence: tuple[str, ...] = ()
    detail: str = ""


class AlertRule(BaseModel):
    model_config = ConfigDict(frozen=True)

    rule_id: str
    component: str
    trigger_statuses: tuple[str, ...]
    severity: Severity
    dedupe_seconds: int = 300


class AlertEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    alert_id: str
    fingerprint: str
    rule_id: str
    severity: Severity
    status: str
    first_seen_at: datetime
    last_seen_at: datetime
    occurrence_count: int = 1
    notification_suppressed: bool = False
    evidence: tuple[str, ...] = ()


class IncidentEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    evidence_id: str
    source: str
    content_hash: str
    observed_at: datetime
    detail: str = ""


class IncidentEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str
    incident_id: str
    from_state: IncidentState | None
    to_state: IncidentState
    actor_id: str
    occurred_at: datetime
    rationale: str = ""
    evidence_ids: tuple[str, ...] = ()


class Incident(BaseModel):
    model_config = ConfigDict(frozen=True)

    incident_id: str
    fingerprint: str
    severity: Severity
    state: IncidentState
    opened_at: datetime
    updated_at: datetime
    alert_ids: tuple[str, ...] = ()
    evidence: tuple[IncidentEvidence, ...] = ()
    events: tuple[IncidentEvent, ...] = ()
    closure_rationale: str = ""


class ResponseAction(BaseModel):
    model_config = ConfigDict(frozen=True)

    action_id: str
    kind: ResponseActionKind
    incident_id: str
    requested_at: datetime
    actor_id: str
    idempotency_key: str
    verified: bool = False
    detail: str = ""


class OperationalSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    captured_at: datetime
    signals: tuple[HealthSignal, ...]
    alerts: tuple[AlertEvent, ...]
    incidents: tuple[Incident, ...]
    actions: tuple[ResponseAction, ...]
    note: str = "Operations visibility only; no alpha, sizing, or order routing."


class EscalationPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    policy_id: str = "live-ops-v3.8"
    allow_automatic_kill_switch: bool = False
    notification_interval_seconds: int = 300
    note: str = "Automatic resume is prohibited."
