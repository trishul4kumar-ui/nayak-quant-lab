"""Digital-twin types. Simulated fill ≠ broker confirmation."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TwinMode(StrEnum):
    HISTORICAL_REPLAY = "historical_replay"
    REALTIME_SHADOW = "realtime_shadow"
    PAPER_REPLAY = "paper_replay"
    FAILURE_INJECTION = "failure_injection"
    COUNTERFACTUAL = "counterfactual"
    DETERMINISM_TEST = "determinism_test"


class FailureKind(StrEnum):
    FEED_DISCONNECT = "feed_disconnect"
    STALE_MARKET = "stale_market"
    SEQUENCE_GAP = "sequence_gap"
    CLOCK_JUMP = "clock_jump"
    MISSING_VOLUME = "missing_volume"
    MISSING_QUOTE = "missing_quote"
    MODEL_UNAVAILABLE = "model_unavailable"
    RISK_DATA_MISSING = "risk_data_missing"
    PORTFOLIO_INFEASIBLE = "portfolio_infeasible"
    PAPER_FILL_FAILURE = "paper_fill_failure"
    DUPLICATE_FILL = "duplicate_fill"
    OUT_OF_ORDER_EVENT = "out_of_order_event"
    RECONCILIATION_BREAK = "reconciliation_break"
    DISK_PRESSURE = "disk_pressure"
    PROCESS_RESTART = "process_restart"


class FailureResponse(StrEnum):
    DEGRADE = "degrade"
    ABSTAIN = "abstain"
    HALT = "halt"
    RECONCILE = "reconcile"
    RECOVER = "recover"


class TwinEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str
    event_type: str
    event_time: datetime
    sequence: int
    run_id: str
    parent_event_id: str = ""
    payload_hash: str
    state_hash_before: str
    state_hash_after: str
    extras: dict[str, Any] = Field(default_factory=dict)


class TwinCheckpoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    checkpoint_id: str
    run_id: str
    kind: str
    state_hash: str
    sequence: int
    event_time: datetime
    note: str = "Checkpoint is not a broker snapshot."


class TwinRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    mode: TwinMode
    state: str
    snapshot_hash: str
    decision_hash: str
    portfolio_hash: str
    fill_hash: str
    account_hash: str
    reconciliation_hash: str
    state_hash: str
    events: tuple[TwinEvent, ...]
    checkpoints: tuple[TwinCheckpoint, ...]
    failure: FailureKind | None = None
    response: FailureResponse | None = None
    counterfactual: bool = False
    live_trading: bool = False
    write_enabled: bool = False
    extras: dict[str, Any] = Field(default_factory=dict)
    note: str = "SHADOW ≠ PAPER ≠ LIVE. DIGITAL TWIN ≠ BROKER."
