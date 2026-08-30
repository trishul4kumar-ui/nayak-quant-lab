"""Frozen safety identities. Material input changes invalidate authorization."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from quantlab.safety.gate_results import GateResult
from quantlab.safety.state import SafetyState


class ActorKind(StrEnum):
    HUMAN = "human"
    AI_SUGGESTION = "ai_suggestion"
    SYSTEM = "system"


class KillScope(StrEnum):
    GLOBAL = "global"
    ACCOUNT = "account"
    STRATEGY = "strategy"
    SYMBOL = "symbol"
    BUY = "buy"
    SELL = "sell"
    NEW_ORDER = "new_order"
    MODIFY_ORDER = "modify_order"
    CANCEL_ORDER = "cancel_order"
    LIVE_RELEASE = "live_release"


class ReconStatus(StrEnum):
    RECONCILED = "reconciled"
    PENDING = "pending"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"
    EMERGENCY = "emergency"


class SafetyRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: str = "SAF-REQ-001"
    idempotency_key: str = "idem-default"
    live_release: bool = False
    as_of: datetime = datetime(2024, 1, 2, tzinfo=UTC)
    decision_hash: str = "dec-hash"
    target_portfolio_hash: str = "tgt-hash"
    order_plan_hash: str = "plan-hash"
    certification_id: str = ""
    certification_state: str = ""
    certification_expired: bool = False
    research_gate_failed: bool = False
    shadow_cycle_id: str = ""
    paper_evidence_id: str = ""
    market_snapshot_hash: str = ""
    account_state_hash: str = ""
    risk_state: str = "unknown"
    risk_unknown: bool = True
    risk_violation: bool = False
    recon_status: ReconStatus = ReconStatus.UNKNOWN
    quantity: float = 0.0
    side: str = "buy"
    symbol: str = "AAA"
    security_id: str = "SEC-AAA"
    price: float = 100.0
    order_type: str = "limit"
    decision_age_ms: float = 0.0
    authorization_age_ms: float = 0.0
    max_age_ms: float = 300_000.0
    ai_override: bool = False
    actor: ActorKind = ActorKind.SYSTEM
    human_approval_id: str = ""
    mutated_target: bool = False
    mutated_decision: bool = False
    mutated_order_plan: bool = False
    mutated_authorization: bool = False
    future_market: bool = False
    future_account: bool = False
    future_risk: bool = False
    policy_id: str = "safety-policy-v1"
    tca_policy_id: str = ""
    account_id: str = "research-account"
    nonce: str = "nonce-1"
    note: str = "Safety request. Not a broker order."


class KillSwitch(BaseModel):
    model_config = ConfigDict(frozen=True)

    switch_id: str
    scope: KillScope
    reason: str
    created_at: datetime
    created_by: str
    activation_source: str
    active: bool
    timestamp: datetime
    audit_hash: str


class HumanApproval(BaseModel):
    model_config = ConfigDict(frozen=True)

    approval_id: str
    actor: ActorKind = ActorKind.HUMAN
    reason: str
    timestamp: datetime
    scope: str = "arm"
    note: str = "Human approval cannot bypass safety gates."


class ExecutionAuthorization(BaseModel):
    model_config = ConfigDict(frozen=True)

    authorization_id: str
    decision_hash: str
    target_portfolio_hash: str
    order_plan_hash: str
    paper_evidence_id: str
    shadow_evidence_id: str
    certification_id: str
    risk_snapshot_ref: str
    data_snapshot_ref: str
    tca_policy_ref: str
    account_identity: str
    execution_policy_identity: str
    system_state: str
    created_at: datetime
    expires_at: datetime
    version: str
    nonce: str
    authorization_hash: str
    live_release: bool = False
    release_allowed: bool = False
    actor: ActorKind = ActorKind.HUMAN
    note: str = "Authorization is not a broker submit."


class SafetyIncident(BaseModel):
    model_config = ConfigDict(frozen=True)

    incident_id: str
    kind: str
    detail: str
    timestamp: datetime


class SafetyResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    evaluation_id: str
    state: SafetyState
    gates: tuple[GateResult, ...]
    live_trading: bool = False
    live_release_authorized: bool = False
    broker_routing_enabled: bool = False
    blocked: bool = True
    authorization: ExecutionAuthorization | None = None
    incidents: tuple[SafetyIncident, ...] = ()
    result_hash: str = ""
    extras: dict[str, Any] = Field(default_factory=dict)
    note: str = "G15 always BLOCK while LIVE_TRADING=false."

    def gate(self, gate_id: str) -> GateResult | None:
        for item in self.gates:
            if item.gate_id.value == gate_id:
                return item
        return None
