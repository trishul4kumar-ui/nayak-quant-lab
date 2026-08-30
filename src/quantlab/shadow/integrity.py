"""Shadow leak flags. PASS/FAIL lives in quantlab.research.integrity."""

from __future__ import annotations

from pydantic import BaseModel


class ShadowLeakFlags(BaseModel):
    future_shadow_data: bool | None = None
    future_decision_input: bool | None = None
    future_execution_input: bool | None = None
    stale_data_decision: bool | None = None
    unknown_calendar_execution: bool | None = None
    duplicate_cycle: bool | None = None
    duplicate_shadow_order: bool | None = None
    shadow_live_confusion: bool | None = None
    live_route_attempt: bool | None = None
    paper_shadow_state_confusion: bool | None = None
    target_mutation: bool | None = None
    decision_mutation: bool | None = None
    snapshot_mutation: bool | None = None
    model_version_mutation: bool | None = None
    configuration_mutation: bool | None = None
    pre_arrival_shadow_fill: bool | None = None
    future_shadow_fill: bool | None = None
    partial_fill_hidden: bool | None = None
    shadow_accounting_break: bool | None = None
    shadow_reconciliation_break: bool | None = None
    checkpoint_hash_mismatch: bool | None = None
    recovery_without_reconciliation: bool | None = None
    certification_expired: bool | None = None
    certification_bypass: bool | None = None
    kill_switch_bypass: bool | None = None
    risk_bypass: bool | None = None
    ai_safety_override: bool | None = None
    synthetic_production_confusion: bool | None = None
    observed_tca_confusion: bool | None = None
    broker_confirmation_confusion: bool | None = None
