"""Canonical hashes for paper OMS objects. Timestamps are identity only when frozen."""

from __future__ import annotations

from typing import Any

from quantlab.backtest.spec import config_hash
from quantlab.paper_oms.models import (
    OMSRun,
    OrderIntent,
    OrderPlan,
    PaperFill,
    PaperOrder,
    ReconciliationReport,
)


def _dump(payload: dict[str, Any]) -> str:
    return config_hash(payload)


def hash_intent(intent: OrderIntent) -> str:
    return _dump(
        intent.model_dump(
            mode="json",
            exclude={"intent_hash", "intent_id", "note"},
        )
    )


def hash_intents(intents: list[OrderIntent]) -> str:
    rows = [item.intent_hash or hash_intent(item) for item in intents]
    return _dump({"intents": sorted(rows)})


def hash_plan(plan: OrderPlan) -> str:
    return _dump(
        plan.model_dump(
            mode="json",
            exclude={"order_plan_hash", "order_plan_id", "note"},
        )
    )


def hash_order(order: PaperOrder) -> str:
    return _dump(
        order.model_dump(
            mode="json",
            exclude={"order_hash", "order_id", "state", "fill_time", "rejection_reason", "note"},
        )
    )


def hash_fill(fill: PaperFill) -> str:
    return _dump(fill.model_dump(mode="json", exclude={"fill_hash", "note"}))


def hash_reconciliation(report: ReconciliationReport) -> str:
    return _dump(
        report.model_dump(mode="json", exclude={"reconciliation_hash", "report_id", "note"})
    )


def hash_run(run: OMSRun) -> str:
    return _dump(
        run.model_dump(
            mode="json",
            exclude={"run_hash", "oms_run_id", "note"},
        )
    )


def idempotency_key(
    *,
    decision_hash: str,
    account_id: str,
    snapshot_id: str,
    execution_policy_id: str,
    plan_hash: str,
) -> str:
    return _dump(
        {
            "decision_hash": decision_hash,
            "account_id": account_id,
            "snapshot_id": snapshot_id,
            "execution_policy_id": execution_policy_id,
            "plan_hash": plan_hash,
        }
    )
