"""Shadow operating modes, sessions, and lifecycle states. Never live."""

from enum import StrEnum


class ShadowMode(StrEnum):
    OFF = "off"
    RESEARCH_PAPER = "research_paper"
    PAPER = "paper"
    SHADOW = "shadow"
    PAUSED = "paused"
    HALTED = "halted"
    ERROR = "error"
    RECOVERY = "recovery"


class CycleStatus(StrEnum):
    CREATED = "created"
    VALIDATED = "validated"
    SNAPSHOT_FROZEN = "snapshot_frozen"
    EXECUTED = "executed"
    RECONCILED = "reconciled"
    COMPLETED = "completed"
    ABSTAINED = "abstained"
    REJECTED = "rejected"
    FAILED = "failed"
    HALTED = "halted"


class ShadowOrderStatus(StrEnum):
    CREATED = "created"
    VALIDATED = "validated"
    SIMULATED = "simulated"
    PARTIAL = "partial"
    COMPLETED = "completed"
    RECONCILED = "reconciled"
    ABSTAINED = "abstained"
    REJECTED = "rejected"


class SessionState(StrEnum):
    PRE_OPEN = "pre_open"
    OPEN = "open"
    CONTINUOUS = "continuous"
    AUCTION = "auction"
    CLOSE = "close"
    POST_CLOSE = "post_close"
    HOLIDAY = "holiday"
    HALT = "halt"
    UNKNOWN = "unknown"


class TriggerKind(StrEnum):
    BAR_CLOSE = "bar_close"
    SCHEDULED_INTERVAL = "scheduled_interval"
    EVENT = "event"
    MANUAL_PAPER_RUN = "manual_paper_run"
    RECOVERY_REPLAY = "recovery_replay"


class StalePolicy(StrEnum):
    ABSTAIN = "abstain"
    PAUSE = "pause"
    HALT = "halt"


class KillReason(StrEnum):
    MANUAL_HALT = "manual_halt"
    DATA_STALE = "data_stale"
    CALENDAR_UNKNOWN = "calendar_unknown"
    RECONCILIATION_BREAK = "reconciliation_break"
    PAPER_ACCOUNTING_BREAK = "paper_accounting_break"
    MODEL_INTEGRITY_FAIL = "model_integrity_fail"
    RISK_LIMIT_BREACH = "risk_limit_breach"
    CAPITAL_DECISION_INVALID = "capital_decision_invalid"
    EXECUTION_INTEGRITY_FAIL = "execution_integrity_fail"
    CONFIGURATION_MISMATCH = "configuration_mismatch"
    CLOCK_SKEW = "clock_skew"
    RECOVERY_INCOMPLETE = "recovery_incomplete"
    CERTIFICATION_INVALID = "certification_invalid"
    LIVE_ROUTE_ATTEMPT = "live_route_attempt"


class IncidentKind(StrEnum):
    DATA_STALE = "data_stale"
    DATA_CONFLICT = "data_conflict"
    SYMBOL_UNRESOLVED = "symbol_unresolved"
    CALENDAR_UNKNOWN = "calendar_unknown"
    MODEL_FAILURE = "model_failure"
    RISK_BREACH = "risk_breach"
    CAPITAL_FAILURE = "capital_failure"
    EXECUTION_FAILURE = "execution_failure"
    RECONCILIATION_BREAK = "reconciliation_break"
    CHECKPOINT_CORRUPTION = "checkpoint_corruption"
    CLOCK_SKEW = "clock_skew"
    CERTIFICATION_EXPIRED = "certification_expired"
    UNSAFE_CONFIGURATION = "unsafe_configuration"


class IncidentSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReplayOutcome(StrEnum):
    MATCH = "match"
    MISMATCH = "mismatch"


class Score(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_TESTED = "not_tested"


class PositionBook(StrEnum):
    SHADOW_POSITION = "shadow_position"
    PAPER_POSITION = "paper_position"
    BROKER_POSITION = "broker_position"


class ResultKind(StrEnum):
    RESEARCH_RESULT = "research_result"
    PAPER_RESULT = "paper_result"
    SHADOW_RESULT = "shadow_result"
    BROKER_OBSERVATION = "broker_observation"
    LIVE_RESULT = "live_result"
