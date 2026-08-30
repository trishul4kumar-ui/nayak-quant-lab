"""App-layer live-certification gate. Qt cannot certify or enable live."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from quantlab.core.errors import QuantLabError
from quantlab.release.audit import history
from quantlab.release.service import (
    approve,
    audit_history,
    certify,
    create,
    default_passing_request,
    evaluate,
    expire,
    inspect,
    last_result,
    list_packages,
    reject,
    revoke,
    suspend,
    waivers,
)
from quantlab.release.state import current


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _safe(fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return fn()
    except QuantLabError as exc:
        return {
            "error": str(exc),
            "live_trading": False,
            "live_enabled": False,
            "certified_is_not_live": True,
        }


def status_payload() -> dict[str, Any]:
    result = last_result() or evaluate()
    return {
        "state": current().value,
        "live_trading": False,
        "live_enabled": False,
        "blocked": result.blocked,
        "evaluation_id": result.evaluation_id,
        "hash": result.result_hash,
        "note": "CERTIFIED ≠ LIVE_ENABLED ≠ BROKER_CONNECTED",
    }


def list_payload() -> list[dict[str, Any]]:
    rows = [
        {
            "id": item.evaluation_id,
            "state": item.state.value,
            "blocked": item.blocked,
            "live_trading": False,
        }
        for item in list_packages()
    ]
    if not rows:
        rows.append({"note": "No live-certification packages.", "live_trading": False})
    return rows


def inspect_payload(item_id: str = "last") -> dict[str, Any]:
    result = inspect(item_id) or evaluate()
    return _dump(result)


def create_payload() -> dict[str, Any]:
    return _dump(create())


def evidence_payload() -> dict[str, Any]:
    result = last_result() or evaluate()
    return {
        "criteria": [_dump(item) for item in result.criteria],
        "live_trading": False,
    }


def validate_payload() -> dict[str, Any]:
    return _dump(evaluate())


def review_payload() -> dict[str, Any]:
    return status_payload()


def approve_payload() -> dict[str, Any]:
    return _safe(lambda: _dump(approve(default_passing_request())))


def reject_payload() -> dict[str, Any]:
    return _dump(reject())


def certify_payload() -> dict[str, Any]:
    return _safe(lambda: _dump(certify(default_passing_request())))


def audit_payload() -> dict[str, Any]:
    return {"count": len(history()), "live_trading": False}


def expire_payload() -> dict[str, Any]:
    return _dump(expire())


def suspend_payload() -> dict[str, Any]:
    return _dump(suspend())


def revoke_payload() -> dict[str, Any]:
    return _dump(revoke())


def waivers_payload() -> dict[str, Any]:
    return {"waivers": [_dump(item) for item in waivers()], "live_trading": False}


def manifest_payload() -> dict[str, Any]:
    result = last_result()
    if result is None or result.manifest is None:
        return {"note": "No release manifest. Eligibility is not live.", "live_trading": False}
    return _dump(result.manifest)


def report_payload() -> dict[str, Any]:
    return inspect_payload()


def lineage_payload() -> dict[str, Any]:
    return {
        "count": len(audit_history()),
        "live_trading": False,
        "note": "Failed certification attempts are retained.",
    }


def readiness_payload() -> dict[str, Any]:
    result = last_result() or evaluate()
    blocked = [item.criterion_id for item in result.criteria if item.blocks]
    return {
        "blocked_criteria": blocked,
        "live_trading": False,
        "live_enabled": False,
    }


def last_run_row() -> dict[str, Any] | None:
    result = last_result()
    if result is None:
        return None
    return {
        "id": result.evaluation_id,
        "state": result.state.value,
        "blocked": result.blocked,
        "hash": result.result_hash,
        "criteria": len(result.criteria),
    }


def run_payload() -> dict[str, Any]:
    return _dump(evaluate())
