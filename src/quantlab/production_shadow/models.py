"""Immutable production-shadow evidence contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EvidenceLabel(StrEnum):
    OBSERVED = "OBSERVED"
    COUNTERFACTUAL = "COUNTERFACTUAL"
    SIMULATED = "SIMULATED"
    MODELLED = "MODELLED"
    CALIBRATED = "CALIBRATED"
    STRESSED = "STRESSED"
    NOT_TESTED = "NOT_TESTED"


class ShadowProductionState(StrEnum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    HALTED = "HALTED"
    BLOCKED = "BLOCKED"


class ShadowCheckResult(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_TESTED = "NOT_TESTED"


class ProductionShadowPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    policy_version: str = "3.5.0"
    market_broker_alignment_seconds: float = 5.0
    minimum_sessions: int | None = None
    require_deterministic_replay: bool = True
    require_production_provenance: bool = True


class ShadowCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    check_id: str
    result: ShadowCheckResult
    critical: bool
    reason: str
    evidence_hash: str = ""

    @property
    def blocks(self) -> bool:
        return self.critical and self.result is not ShadowCheckResult.PASS


class ProductionShadowIncident(BaseModel):
    model_config = ConfigDict(frozen=True)

    incident_id: str
    severity: str
    detected_at: datetime
    source: str
    description: str
    evidence: tuple[str, ...] = ()
    state: str = "OPEN"
    owner: str = "unassigned"
    resolution: str = ""


class ProductionShadowReadiness(BaseModel):
    model_config = ConfigDict(frozen=True)

    dimensions: dict[str, ShadowCheckResult] = Field(default_factory=dict)
    critical_failures: tuple[str, ...] = ()
    note: str = "No aggregate score can conceal a critical readiness failure."


class ProductionShadowRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    shadow_run_id: str
    market_snapshot_hash: str = ""
    broker_snapshot_hash: str = ""
    strategy_release_hash: str = ""
    decision_hash: str = ""
    target_portfolio_hash: str = ""
    paper_order_plan_hash: str = ""
    execution_policy_hash: str = ""
    twin_state_hash: str = ""
    reconciliation_hash: str = ""
    policy: ProductionShadowPolicy
    checks: tuple[ShadowCheck, ...]
    incidents: tuple[ProductionShadowIncident, ...] = ()
    readiness: ProductionShadowReadiness
    observed_at: datetime
    state: ShadowProductionState
    evidence_labels: dict[str, EvidenceLabel] = Field(default_factory=dict)
    run_hash: str
    live_trading: bool = False
    broker_write_enabled: bool = False
    non_routable: bool = True
    note: str = "Production shadow is evidence only: simulated orders never reach a broker."
