"""App-layer paper OMS services. CLI and desktop call these. UI does not simulate fills."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantlab.capital.memory import get_result as get_capital_result
from quantlab.capital.memory import last_result as last_capital
from quantlab.core.config import get_settings
from quantlab.paper_oms.enums import EventType, OrderLifecycleState
from quantlab.paper_oms.experiment import run_paper_experiment
from quantlab.paper_oms.library import seed_account, seed_decision, seed_snapshot, seed_target
from quantlab.paper_oms.orders import advance
from quantlab.paper_oms.policy import list_policies
from quantlab.paper_oms.reporting import lifecycle_rows, result_report
from quantlab.paper_oms.state import (
    get_account,
    get_result,
    last_result,
    list_events,
    list_orders,
    list_runs,
    persist,
    put_account,
    replace_order,
)


def _ledger_path(raw: str) -> Path:
    if raw:
        return Path(raw)
    return Path(get_settings().experiment_ledger_path)


def _inputs(decision_id: str) -> tuple[Any, Any]:
    capital = get_capital_result(decision_id) if decision_id not in {"", "last"} else last_capital()
    if capital is not None:
        return capital.decision, capital.target
    return seed_decision(), seed_target()


def list_payload() -> list[dict[str, Any]]:
    rows = []
    for run in list_runs():
        rows.append(
            {
                "oms_run_id": run.oms_run_id,
                "status": run.status.value,
                "decision_hash": run.decision_hash,
                "reconciliation": run.reconciliation_status.value,
                "live_trading": False,
                "note": "Paper OMS run. Not live.",
            }
        )
    if not rows:
        rows.append(
            {
                "note": "No paper runs yet. quantlab paper submit last",
                "live_trading": False,
            }
        )
    return rows


def inspect_payload(run_id: str) -> dict[str, Any]:
    result = get_result(run_id)
    if result is None:
        return {"error": "no paper OMS run yet; run quantlab paper submit"}
    payload = result.run.model_dump(mode="json")
    payload["live_trading"] = False
    payload["note"] = "Paper inspect. Fills are simulated."
    return payload


def create_payload() -> dict[str, Any]:
    account = put_account(seed_account())
    persist()
    return {
        "account_id": account.account_id,
        "cash": account.cash,
        "equity": account.equity,
        "live_trading": False,
        "note": "Seed paper account created. Not a broker account.",
    }


def plan_payload(decision_id: str, *, policy: str = "base") -> dict[str, Any]:
    from quantlab.paper_oms.intent import intents_from_target
    from quantlab.paper_oms.planner import plan_orders
    from quantlab.paper_oms.policy import resolve_policy

    decision, target = _inputs(decision_id)
    account = get_account("PAPER-001") or seed_account()
    snapshot = seed_snapshot()
    intents = intents_from_target(decision, target, account, snapshot)
    plan = plan_orders(intents, account, snapshot, resolve_policy(policy))
    return {
        "order_plan_id": plan.order_plan_id,
        "order_plan_hash": plan.order_plan_hash,
        "intent_hash": plan.intent_hash,
        "instructions": [item.model_dump(mode="json") for item in plan.instructions],
        "residuals": plan.residuals,
        "live_trading": False,
        "note": "Paper plan only. Not submitted.",
    }


def validate_payload(plan_id: str) -> dict[str, Any]:
    del plan_id
    return {
        "valid": True,
        "live_trading": False,
        "note": "Validation runs on submit. Official NSE holidays remain NOT_TESTED.",
    }


def submit_payload(decision_id: str, *, policy: str = "base", ledger: str = "") -> dict[str, Any]:
    from quantlab.paper_oms.models import PaperOMSRequest

    decision, target = _inputs(decision_id)
    result, run = run_paper_experiment(
        PaperOMSRequest(execution_policy_id=policy, decision_id=decision.decision_id),
        ledger_path=_ledger_path(ledger),
        decision=decision,
        target=target,
    )
    summary: dict[str, Any] = {
        "oms_run_id": result.run.oms_run_id,
        "status": result.run.status.value,
        "decision_id": decision.decision_id,
        "order_count": result.run.order_count,
        "fill_count": result.run.fill_count,
        "reconciliation": result.reconciliation.status.value,
        "weights_vs_positions": [gap.model_dump(mode="json") for gap in result.reconciliation.gaps],
        "live_trading": False,
        "selection_stage": run.selection_stage,
        "note": "Paper submit. Simulated fills. Not broker-confirmed.",
    }
    try:
        from quantlab.knowledge.ingest import persist_paper_oms

        persist_paper_oms(result, decision, _ledger_path(ledger))
    except Exception as exc:  # noqa: BLE001 — knowledge must not fail a recorded paper run
        summary["knowledge_ingest"] = f"WARN: {exc}"
    return summary


def fills_payload(run_id: str) -> dict[str, Any]:
    result = get_result(run_id)
    if result is None:
        return {"error": "no paper OMS run yet"}
    return {
        "fills": [item.model_dump(mode="json") for item in result.fills],
        "live_trading": False,
        "note": "Simulated paper fills. Not LIVE FILLED. Not BROKER CONFIRMED.",
    }


def positions_payload(account_id: str) -> dict[str, Any]:
    account = get_account(account_id)
    if account is None:
        last = last_result()
        account = None if last is None else last.account
    if account is None:
        return {"error": "no paper account yet"}
    return {
        "account_id": account.account_id,
        "positions": [item.model_dump(mode="json") for item in account.positions.values()],
        "equity": account.equity,
        "live_trading": False,
    }


def cash_payload(account_id: str) -> dict[str, Any]:
    account = get_account(account_id)
    if account is None:
        last = last_result()
        account = None if last is None else last.account
    if account is None:
        return {"error": "no paper account yet"}
    return {
        "cash": account.cash,
        "reserved_cash": account.reserved_cash,
        "available_cash": account.available_cash,
        "ledger": None if account.ledger is None else account.ledger.model_dump(mode="json"),
        "live_trading": False,
        "note": "Paper cash. Not a live broker balance.",
    }


def reconcile_payload(run_id: str) -> dict[str, Any]:
    result = get_result(run_id)
    if result is None:
        return {"error": "no paper OMS run yet"}
    payload = result.reconciliation.model_dump(mode="json")
    payload["live_trading"] = False
    return payload


def orders_payload(run_id: str) -> dict[str, Any]:
    result = get_result(run_id)
    orders = result.orders if result is not None else list_orders(run_id)
    return {
        "orders": lifecycle_rows(orders),
        "live_trading": False,
    }


def events_payload(order_id: str) -> dict[str, Any]:
    if not order_id:
        result = last_result()
        if result is None or not result.orders:
            return {"events": []}
        order_id = result.orders[0].order_id
    return {
        "events": [item.model_dump(mode="json") for item in list_events(order_id)],
        "live_trading": False,
    }


def cancel_payload(order_id: str) -> dict[str, Any]:
    result = last_result()
    if result is None:
        return {"error": "no paper OMS run yet"}
    found = next((item for item in result.orders if item.order_id == order_id), None)
    if found is None:
        return {"error": f"unknown paper order {order_id}"}
    events = list(result.events)
    cancelled = advance(
        found,
        OrderLifecycleState.CANCELLED,
        events,
        EventType.ORDER_CANCELLED,
        reason="paper cancel",
    )
    replace_order(cancelled)
    persist()
    return {
        "order_id": cancelled.order_id,
        "state": cancelled.state.value,
        "remaining": cancelled.remaining_quantity,
        "live_trading": False,
        "note": "CANCEL PAPER. Not a live cancel.",
    }


def report_payload(run_id: str) -> dict[str, Any]:
    result = get_result(run_id)
    if result is None:
        return {"error": "no paper OMS run yet"}
    return result_report(result)


def tca_payload(run_id: str) -> dict[str, Any]:
    result = get_result(run_id)
    if result is None:
        return {"error": "no paper OMS run yet"}
    payload = result.tca.model_dump(mode="json")
    payload["live_trading"] = False
    return payload


def residuals_payload(run_id: str) -> dict[str, Any]:
    result = get_result(run_id)
    if result is None:
        return {"error": "no paper OMS run yet"}
    return {
        "plan_residuals": result.plan.residuals,
        "order_remaining": {
            item.security_id: item.remaining_quantity + item.residual_quantity
            for item in result.orders
        },
        "live_trading": False,
    }


def exceptions_payload(run_id: str) -> dict[str, Any]:
    result = get_result(run_id)
    if result is None:
        return {"exceptions": []}
    return {"exceptions": result.exceptions, "breaks": result.reconciliation.breaks}


def audit_payload(run_id: str) -> dict[str, Any]:
    result = get_result(run_id)
    if result is None:
        return {"error": "no paper OMS run yet"}
    return {
        "oms_run_id": result.run.oms_run_id,
        "decision_id": result.decision_id,
        "decision_hash": result.run.decision_hash,
        "intent_hash": result.run.intent_hash,
        "order_plan_hash": result.run.order_plan_hash,
        "run_hash": result.run.run_hash,
        "reconciliation_hash": result.reconciliation.reconciliation_hash,
        "events": len(result.events),
        "live_trading": False,
        "note": "Paper audit trail. No broker path.",
    }


def policy_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    for item in list_policies():
        rows.append([item.policy_id, item.scenario_id, item.model_id, str(item.random_seed)])
    return rows


def last_run_row() -> dict[str, Any] | None:
    result = last_result()
    if result is None:
        return None
    return {
        "id": result.run.oms_run_id,
        "status": result.run.status.value,
        "recon": result.reconciliation.status.value,
        "orders": result.run.order_count,
        "fills": result.run.fill_count,
        "cash": result.account.cash,
        "hash": result.run.run_hash,
    }
