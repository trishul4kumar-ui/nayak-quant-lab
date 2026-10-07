"""Immutable Phase 49 desk state; all jobs remain research or paper workflows."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import AwareDatetime, Field, model_validator

from quantlab.agents.hashing import Artifact


class DeskPhase(StrEnum):
    OFF = "OFF"
    STARTING = "STARTING"
    PRE_MARKET = "PRE_MARKET"
    OPENING_OBSERVATION = "OPENING_OBSERVATION"
    INTRADAY_RESEARCH = "INTRADAY_RESEARCH"
    POSITION_MONITORING = "POSITION_MONITORING"
    CLOSING_REVIEW = "CLOSING_REVIEW"
    POST_MARKET_RESEARCH = "POST_MARKET_RESEARCH"
    DAILY_RECONCILIATION = "DAILY_RECONCILIATION"
    LEARNING_REVIEW = "LEARNING_REVIEW"
    COMPLETE = "COMPLETE"
    PAUSED = "PAUSED"
    DEGRADED = "DEGRADED"
    HALTED = "HALTED"
    ERROR = "ERROR"


class DeskSession(StrEnum):
    CLOSED = "CLOSED"
    PRE_MARKET = "PRE_MARKET"
    OPENING = "OPENING"
    CONTINUOUS = "CONTINUOUS"
    CLOSING = "CLOSING"
    POST_MARKET = "POST_MARKET"


class DeskJobType(StrEnum):
    DATA_HEALTH = "DATA_HEALTH"
    UNIVERSE_REFRESH = "UNIVERSE_REFRESH"
    BULL_SCAN = "BULL_SCAN"
    BEAR_SCAN = "BEAR_SCAN"
    DEBATE = "DEBATE"
    CANDIDATE_REFRESH = "CANDIDATE_REFRESH"
    POSITION_REVIEW = "POSITION_REVIEW"
    DAILY_RECONCILIATION = "DAILY_RECONCILIATION"


class DeskJobStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class NotificationSeverity(StrEnum):
    INFORMATION = "INFORMATION"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    CRITICAL = "CRITICAL"


class DailyDeskPolicy(Artifact):
    policy_id: str
    max_agent_runs_per_interval: int = Field(ge=1, le=100)
    max_concurrent_model_calls: int = Field(ge=0, le=20)
    max_tool_calls_per_run: int = Field(ge=0, le=50)
    max_debate_rounds: int = Field(ge=0, le=4)
    candidate_refresh_cooldown_seconds: int = Field(ge=60, le=86_400)
    repeated_failure_cooldown_seconds: int = Field(ge=60, le=86_400)
    maximum_research_jobs_per_tick: int = Field(ge=1, le=100)


class DailyDeskState(Artifact):
    desk_id: str = Field(min_length=1, max_length=160)
    session_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    calendar_version: str = Field(min_length=1, max_length=160)
    calendar_provenance: str = Field(min_length=1, max_length=500)
    session: DeskSession
    phase: DeskPhase
    policy_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    paused: bool = False
    degraded_reason: str | None = Field(default=None, max_length=500)
    last_snapshot_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    completed_job_ids: tuple[str, ...] = Field(max_length=5_000)
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def coherent_state(self) -> Self:
        if self.paused != (self.phase is DeskPhase.PAUSED):
            raise ValueError("paused flag and phase must agree")
        if self.phase is DeskPhase.DEGRADED and not self.degraded_reason:
            raise ValueError("degraded desk state requires a reason")
        return self


class DeskJob(Artifact):
    job_id: str = Field(min_length=1, max_length=160)
    job_type: DeskJobType
    priority: int = Field(ge=0, le=100)
    scheduled_for: AwareDatetime
    security_scope: tuple[str, ...] = Field(max_length=500)
    snapshot_dependency_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    safe_research_read: bool = True
    deadline: AwareDatetime | None = None
    status: DeskJobStatus = DeskJobStatus.QUEUED
    attempt_count: int = Field(default=0, ge=0, le=10)
    max_attempts: int = Field(ge=0, le=10)
    last_error_code: str | None = Field(default=None, max_length=160)
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def bounded_retry_policy(self) -> Self:
        if not self.safe_research_read and self.max_attempts:
            raise ValueError("state-changing jobs cannot be retried in the daily desk")
        if self.deadline is not None and self.deadline < self.scheduled_for:
            raise ValueError("job deadline cannot predate its schedule")
        return self


class DeskNotification(Artifact):
    notification_id: str = Field(min_length=1, max_length=160)
    severity: NotificationSeverity
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=1_000)
    candidate_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    dedupe_key: str = Field(min_length=1, max_length=300)
    acknowledged: bool = False
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def actionable_is_bounded(self) -> Self:
        if self.severity is NotificationSeverity.ACTION_REQUIRED and not self.candidate_hash:
            raise ValueError("action-required notification requires a candidate reference")
        return self


class RecoveryReport(Artifact):
    desk_state_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    resumed_job_ids: tuple[str, ...]
    skipped_job_ids: tuple[str, ...]
    stale_candidate_hashes: tuple[str, ...]
    execution_authority: Literal[False] = False


class Watchlist(Artifact):
    watchlist_id: str = Field(min_length=1, max_length=160)
    security_ids: tuple[str, ...] = Field(min_length=1, max_length=500)
    source: str = Field(min_length=1, max_length=300)
    execution_authority: Literal[False] = False
