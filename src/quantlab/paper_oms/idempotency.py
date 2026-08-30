"""Idempotent paper submission. Same inputs return the existing run."""

from __future__ import annotations

from threading import Lock

from quantlab.paper_oms.errors import DuplicateOrderError
from quantlab.paper_oms.identity import idempotency_key
from quantlab.paper_oms.models import OMSRun, OrderPlan


class IdempotencyStore:
    def __init__(self) -> None:
        self._runs: dict[str, OMSRun] = {}
        self._lock = Lock()

    def key_for(self, plan: OrderPlan, *, account_id: str) -> str:
        return idempotency_key(
            decision_hash=plan.decision_hash,
            account_id=account_id,
            snapshot_id=plan.snapshot_id,
            execution_policy_id=plan.execution_policy_id,
            plan_hash=plan.order_plan_hash,
        )

    def lookup(self, key: str) -> OMSRun | None:
        return self._runs.get(key)

    def remember(self, key: str, run: OMSRun) -> OMSRun:
        with self._lock:
            existing = self._runs.get(key)
            if existing is not None:
                return existing
            self._runs[key] = run
            return run

    def require_unique_order(self, key: str, existing: str | None) -> None:
        if existing is not None and existing != key:
            raise DuplicateOrderError("paper order identity collision")
