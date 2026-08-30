"""App-layer safety gateway. Qt cannot authorize live or connect brokers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from quantlab.core.errors import QuantLabError
from quantlab.safety.audit import history, incidents
from quantlab.safety.kill_switch import snapshot
from quantlab.safety.models import KillScope, SafetyRequest
from quantlab.safety.policy import POLICY
from quantlab.safety.repository import get, last, list_results
from quantlab.safety.service import (
    approve_human,
    authorize,
    emergency,
    evaluate_request,
    halt,
    kill,
    recover,
    reject,
    unkill,
)
from quantlab.safety.state import current


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _safe(fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return fn()
    except QuantLabError as exc:
        return {
            "error": str(exc),
            "live_trading": False,
            "live_release_authorized": False,
            "broker_routing_enabled": False,
        }


def status_payload() -> dict[str, Any]:
    result = last() or evaluate_request()
    g15 = result.gate("G15_FINAL_RELEASE")
    return {
        "state": current().value,
        "live_trading": False,
        "live_release_authorized": False,
        "broker_routing_enabled": False,
        "blocked": result.blocked,
        "g15": g15.verdict.value if g15 is not None else "block",
        "evaluation_id": result.evaluation_id,
        "hash": result.result_hash,
    }


def inspect_payload(item_id: str = "last") -> dict[str, Any]:
    result = get(item_id) or last() or evaluate_request()
    return _dump(result)


def gates_payload() -> dict[str, Any]:
    result = last() or evaluate_request()
    return {
        "gates": [_dump(item) for item in result.gates],
        "live_trading": False,
        "blocked": True,
    }


def authorize_payload() -> dict[str, Any]:
    return _safe(lambda: _dump(authorize(SafetyRequest(live_release=False))))


def reject_payload() -> dict[str, Any]:
    return _dump(reject(reason="operator reject"))


def kill_payload(scope: str = "global") -> dict[str, Any]:
    return _dump(kill(KillScope(scope), reason="operator kill"))


def unkill_payload(scope: str = "global") -> dict[str, Any]:
    return _dump(unkill(KillScope(scope), reason="explicit unkill"))


def halt_payload() -> dict[str, Any]:
    return _dump(halt())


def emergency_payload() -> dict[str, Any]:
    return _dump(emergency())


def recover_payload() -> dict[str, Any]:
    return _safe(lambda: _dump(recover()))


def reconcile_payload() -> dict[str, Any]:
    result = last() or evaluate_request()
    gate = result.gate("G9_RECONCILIATION")
    return {
        "verdict": gate.verdict.value if gate else "not_tested",
        "live_trading": False,
        "note": "reconciliation is a barrier; no auto-repair",
    }


def audit_payload() -> dict[str, Any]:
    return {
        "count": len(history()),
        "incidents": [_dump(item) for item in incidents()],
        "live_trading": False,
    }


def policy_payload() -> dict[str, Any]:
    return {**_dump(POLICY), "policy_hash": POLICY.policy_hash(), "live_trading": False}


def validate_payload() -> dict[str, Any]:
    return _dump(evaluate_request())


def explain_payload() -> dict[str, Any]:
    result = last() or evaluate_request()
    blocked = [item.gate_id.value for item in result.gates if item.blocks_release]
    return {
        "blocked_gates": blocked,
        "live_trading": False,
        "note": "UNKNOWN → BLOCK. G15 always BLOCK.",
    }


def last_run_row() -> dict[str, Any] | None:
    result = last()
    if result is None:
        return None
    return {
        "id": result.evaluation_id,
        "state": result.state.value,
        "blocked": result.blocked,
        "hash": result.result_hash,
        "gates": len(result.gates),
    }


def run_payload() -> dict[str, Any]:
    return _dump(evaluate_request())


def list_payload() -> list[dict[str, Any]]:
    rows = [
        {
            "evaluation_id": item.evaluation_id,
            "state": item.state.value,
            "blocked": item.blocked,
            "live_trading": False,
        }
        for item in list_results()
    ]
    if not rows:
        rows.append(
            {"note": "No safety evaluations. quantlab safety status", "live_trading": False}
        )
    return rows


def kills_payload() -> dict[str, Any]:
    return {scope.value: _dump(item) for scope, item in snapshot().items()}


def human_payload() -> dict[str, Any]:
    approval = approve_human(approval_id="human-1", reason="recorded only")
    return _dump(approval)
