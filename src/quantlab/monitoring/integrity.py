"""Monitoring leak flags. PASS/FAIL lives in quantlab.research.integrity."""

from __future__ import annotations

from pydantic import BaseModel


class MonitoringLeakFlags(BaseModel):
    future_performance_mark: bool | None = None
    future_attribution_input: bool | None = None
    future_benchmark: bool | None = None
    future_factor_return: bool | None = None
    performance_snapshot_mutation: bool | None = None
    position_history_mutation: bool | None = None
    pnl_reconciliation_break: bool | None = None
    attribution_reconciliation_break: bool | None = None
    hidden_residual: bool | None = None
    benchmark_lookahead: bool | None = None
    target_observation_confusion: bool | None = None
    posthoc_attribution: bool | None = None
    performance_claim_overstatement: bool | None = None
