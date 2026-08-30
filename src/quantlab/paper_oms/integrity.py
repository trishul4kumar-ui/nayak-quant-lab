"""Paper OMS leak flags. PASS/FAIL lives in quantlab.research.integrity."""

from __future__ import annotations

from pydantic import BaseModel


class PaperOMSLeakFlags(BaseModel):
    target_mutation: bool | None = None
    decision_hash_mismatch: bool | None = None
    order_intent_mutation: bool | None = None
    order_plan_mutation: bool | None = None
    duplicate_order: bool | None = None
    duplicate_fill: bool | None = None
    invalid_order_transition: bool | None = None
    pre_arrival_fill: bool | None = None
    future_execution_price: bool | None = None
    future_fill_information: bool | None = None
    future_liquidity_leak: bool | None = None
    full_fill_assumption: bool | None = None
    hidden_partial_fill: bool | None = None
    cash_accounting_break: bool | None = None
    position_accounting_break: bool | None = None
    target_position_mismatch: bool | None = None
    order_fill_mismatch: bool | None = None
    orphan_fill: bool | None = None
    orphan_event: bool | None = None
    reconciliation_break: bool | None = None
    execution_policy_mutation: bool | None = None
    paper_live_mode_confusion: bool | None = None
    broker_import_violation: bool | None = None
