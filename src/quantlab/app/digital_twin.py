"""App-layer digital twin. Qt cannot send orders or route to a broker."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from quantlab.core.errors import QuantLabError
from quantlab.digital_twin.models import TwinMode
from quantlab.digital_twin.service import (
    audit_history,
    checkpoint,
    compare,
    create,
    halt,
    inject_failure,
    inspect,
    list_runs,
    recover,
    replay,
    run_twin,
)
from quantlab.digital_twin.state import current

_LAST: dict[str, Any] | None = None


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _safe(fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return fn()
    except QuantLabError as exc:
        return {"error": str(exc), "live_trading": False, "write_enabled": False}


def last_run_row() -> dict[str, Any] | None:
    return _LAST


def _store(row: dict[str, Any]) -> dict[str, Any]:
    global _LAST
    _LAST = row
    return row


def _row(item: Any) -> dict[str, Any]:
    return _store(
        {
            "id": item.run_id,
            "mode": item.mode.value,
            "state": item.state,
            "hash": item.state_hash,
            "decision": item.decision_hash,
            "fill": item.fill_hash,
            "counterfactual": item.counterfactual,
            "live_trading": False,
            **_dump(item),
        }
    )


def list_payload() -> list[dict[str, Any]]:
    ids = list_runs()
    if not ids:
        return [{"note": "No twin runs.", "live_trading": False}]
    return [{"id": item, "live_trading": False} for item in ids]


def inspect_payload(item_id: str = "last") -> dict[str, Any]:
    item = inspect(item_id)
    if item is None:
        return {"note": "No twin run yet.", "live_trading": False}
    return _dump(item)


def create_payload(mode: str = "determinism_test") -> dict[str, Any]:
    return _safe(lambda: _row(create(mode)))


def run_payload(mode: str = "determinism_test") -> dict[str, Any]:
    return _safe(lambda: _row(run_twin(mode=mode)))


def pause_payload() -> dict[str, Any]:
    return {"paused": True, "live_trading": False, "note": "Pause has no broker effect."}


def halt_payload() -> dict[str, Any]:
    return _safe(lambda: _row(halt()))


def checkpoint_payload() -> dict[str, Any]:
    return _safe(lambda: _dump(checkpoint()))


def replay_payload() -> dict[str, Any]:
    return _safe(lambda: _row(replay()))


def compare_payload() -> dict[str, Any]:
    return _safe(lambda: dict(compare()))


def reconcile_payload() -> dict[str, Any]:
    item = inspect("last") or run_twin()
    return {
        "reconciliation_hash": item.reconciliation_hash,
        "live_trading": False,
        "note": "Simulated fill ≠ broker confirmation.",
    }


def failures_payload(kind: str = "stale_market") -> dict[str, Any]:
    return _safe(lambda: _row(inject_failure(kind)))


def recovery_payload() -> dict[str, Any]:
    ck = checkpoint()
    return _safe(lambda: _row(recover(ck.checkpoint_id)))


def determinism_payload() -> dict[str, Any]:
    first = run_twin(mode=TwinMode.DETERMINISM_TEST)
    second = replay(first.run_id)
    return {
        "match": first.state_hash == second.state_hash,
        "decision_match": first.decision_hash == second.decision_hash,
        "live_trading": False,
    }


def counterfactual_payload() -> dict[str, Any]:
    item = run_twin(mode=TwinMode.COUNTERFACTUAL)
    return _row(item)


def report_payload() -> dict[str, Any]:
    item = inspect("last") or run_twin()
    return {
        "run_id": item.run_id,
        "mode": item.mode.value,
        "events": len(item.events),
        "live_trading": False,
        "write_enabled": False,
        "state": current().value,
    }


def audit_payload() -> list[dict[str, Any]]:
    return audit_history() or [{"note": "No twin audit yet.", "live_trading": False}]
