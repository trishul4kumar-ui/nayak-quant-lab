"""App-layer shadow engine. Qt cannot route live or connect brokers."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from quantlab.core.config import get_settings
from quantlab.core.errors import QuantLabError
from quantlab.shadow.audit import incidents
from quantlab.shadow.enums import ShadowMode
from quantlab.shadow.experiment import last_experiment_row, run_shadow_experiment
from quantlab.shadow.health import heartbeat, scorecard
from quantlab.shadow.models import ShadowRequest, ShadowResult
from quantlab.shadow.recovery import recover
from quantlab.shadow.reporting import result_report
from quantlab.shadow.service import (
    halt,
    pause,
    replay_cycle,
    resume,
    run_shadow_cycle,
    start,
    stop,
)
from quantlab.shadow.state import get_result, last_result, list_results, mode


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _ledger_path(raw: str) -> Path:
    if raw:
        return Path(raw)
    return Path(get_settings().experiment_ledger_path)


def _ensure_loaded() -> None:
    if last_result() is None:
        with suppress(QuantLabError):
            recover()


def _require(cycle_id: str) -> ShadowResult | None:
    _ensure_loaded()
    if cycle_id in {"", "last"}:
        return last_result()
    return get_result(cycle_id)


def _safe(fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return fn()
    except QuantLabError as exc:
        return {
            "error": str(exc),
            "live_trading": False,
            "shadow_mode": True,
            "broker_routing_enabled": False,
        }


def list_payload() -> list[dict[str, Any]]:
    rows = [
        {
            "cycle_id": item.cycle.cycle_id,
            "mode": item.cycle.mode.value,
            "status": item.cycle.status.value,
            "live_trading": False,
        }
        for item in list_results()
    ]
    if not rows:
        rows.append({"note": "No shadow cycles. quantlab shadow run", "live_trading": False})
    return rows


def inspect_payload(cycle_id: str) -> dict[str, Any]:
    result = _require(cycle_id)
    if result is None:
        return {"error": "no shadow cycle yet", "live_trading": False}
    payload = _dump(result.cycle)
    payload["live_trading"] = False
    payload["note"] = "Inspect. Shadow is not live. Not broker-confirmed."
    return payload


def run_payload(*, mode: str = "research_paper", ledger: str = "") -> dict[str, Any]:
    result, _row = run_shadow_experiment(
        ShadowRequest(mode=ShadowMode(mode)),
        ledger_path=_ledger_path(ledger),
    )
    return result_report(result)


def start_payload(*, mode: str = "research_paper") -> dict[str, Any]:
    return _safe(lambda: {"mode": start(ShadowMode(mode)).value, "live_trading": False})


def stop_payload() -> dict[str, Any]:
    return {"mode": stop().value, "live_trading": False}


def pause_payload() -> dict[str, Any]:
    return _safe(lambda: {"mode": pause().value, "live_trading": False})


def resume_payload(*, mode: str = "research_paper") -> dict[str, Any]:
    return _safe(lambda: {"mode": resume(ShadowMode(mode)).value, "live_trading": False})


def status_payload() -> dict[str, Any]:
    beat = heartbeat()
    return {
        "mode": mode().value,
        "heartbeat": _dump(beat),
        "live_trading": False,
        "shadow_mode": True,
        "broker_routing_enabled": False,
        "note": "healthy-idle is not a dead process",
    }


def cycle_payload(cycle_id: str) -> dict[str, Any]:
    return inspect_payload(cycle_id)


def decision_payload(cycle_id: str) -> dict[str, Any]:
    result = _require(cycle_id)
    if result is None:
        return {"error": "no shadow cycle yet"}
    return {
        "cycle_id": result.cycle.cycle_id,
        "decision_time": result.cycle.decision_time.isoformat(),
        "capital_decision_hash": result.cycle.capital_decision_hash,
        "target_portfolio_hash": result.cycle.target_portfolio_hash,
        "live_trading": False,
    }


def targets_payload(cycle_id: str) -> dict[str, Any]:
    result = _require(cycle_id)
    if result is None:
        return {"error": "no shadow cycle yet"}
    return {
        "target_portfolio_hash": result.cycle.target_portfolio_hash,
        "intents": [item.model_dump(mode="json") for item in result.intents],
        "live_trading": False,
        "note": "Δq = target_qty - current_qty. Not a BUY from weight sign.",
    }


def orders_payload(cycle_id: str) -> dict[str, Any]:
    result = _require(cycle_id)
    if result is None:
        return {"error": "no shadow cycle yet"}
    return {
        "orders": [item.model_dump(mode="json") for item in result.orders],
        "live_trading": False,
        "note": "Shadow orders are not routable.",
    }


def fills_payload(cycle_id: str) -> dict[str, Any]:
    result = _require(cycle_id)
    if result is None:
        return {"error": "no shadow cycle yet"}
    return {
        "fills": [item.model_dump(mode="json") for item in result.fills],
        "live_trading": False,
        "note": "Simulated fills. Not broker-confirmed.",
    }


def positions_payload(cycle_id: str) -> dict[str, Any]:
    result = _require(cycle_id)
    if result is None:
        return {"error": "no shadow cycle yet"}
    return {
        "book": result.portfolio.book.value,
        "positions": {
            name: pos.model_dump(mode="json") for name, pos in result.portfolio.positions.items()
        },
        "live_trading": False,
        "note": "SHADOW_POSITION ≠ PAPER_POSITION ≠ BROKER_POSITION",
    }


def cash_payload(cycle_id: str) -> dict[str, Any]:
    result = _require(cycle_id)
    if result is None:
        return {"error": "no shadow cycle yet"}
    return {
        "cash": result.portfolio.cash,
        "equity": result.portfolio.equity,
        "account_id": result.portfolio.account_id,
        "live_trading": False,
    }


def reconcile_payload(cycle_id: str) -> dict[str, Any]:
    result = _require(cycle_id)
    if result is None:
        return {"error": "no shadow cycle yet"}
    payload = result.reconciliation.model_dump(mode="json")
    payload["live_trading"] = False
    return payload


def health_payload() -> dict[str, Any]:
    result = last_result()
    card = scorecard(result)
    beat = heartbeat()
    return {
        "scorecard": card.model_dump(mode="json"),
        "heartbeat": beat.model_dump(mode="json"),
        "mode": mode().value,
        "live_trading": False,
        "shadow_mode": True,
        "broker_routing_enabled": False,
        "live_order_submission_enabled": False,
        "note": "Scorecard is diagnostic. Not a single ready boolean. Not live.",
    }


def incidents_payload() -> dict[str, Any]:
    return {
        "incidents": [item.model_dump(mode="json") for item in incidents()],
        "live_trading": False,
        "note": "Incidents are retained.",
    }


def latency_payload(cycle_id: str) -> dict[str, Any]:
    result = _require(cycle_id)
    if result is None:
        return {"error": "no shadow cycle yet"}
    payload = result.latency.model_dump(mode="json")
    payload["live_trading"] = False
    return payload


def drift_payload(cycle_id: str) -> dict[str, Any]:
    result = _require(cycle_id)
    if result is None:
        return {"error": "no shadow cycle yet"}
    payload = result.compare.model_dump(mode="json")
    payload["live_trading"] = False
    payload["note"] = "Diagnostic drift. Not a promotion gate."
    return payload


def tca_payload(cycle_id: str) -> dict[str, Any]:
    result = _require(cycle_id)
    if result is None:
        return {"error": "no shadow cycle yet"}
    paper_tca = result.paper.tca.model_dump(mode="json") if result.paper else {}
    paper_tca["kind"] = "modelled"
    paper_tca["live_trading"] = False
    paper_tca["note"] = "MODELLED paper/shadow TCA. Not OBSERVED broker TCA."
    return paper_tca


def compare_payload(cycle_id: str) -> dict[str, Any]:
    return drift_payload(cycle_id)


def checkpoint_payload(cycle_id: str) -> dict[str, Any]:
    result = _require(cycle_id)
    if result is None or result.checkpoint is None:
        return {"error": "no checkpoint yet"}
    payload = result.checkpoint.model_dump(mode="json")
    payload["live_trading"] = False
    return payload


def recover_payload() -> dict[str, Any]:
    return _safe(lambda: result_report(recover()))


def audit_payload(cycle_id: str) -> dict[str, Any]:
    result = _require(cycle_id)
    return {
        "cycle": inspect_payload(cycle_id),
        "incidents": incidents_payload(),
        "broker_imports": False,
        "live_trading": False,
        "shadow_mode": True,
        "broker_routing_enabled": False,
        "live_order_submission_enabled": False,
        "note": "ZERO LIVE BROKER ROUTING. Audit is not a live enablement.",
        "integrity": result.integrity.as_str_map() if result else {},
    }


def report_payload(cycle_id: str) -> dict[str, Any]:
    result = _require(cycle_id)
    if result is None:
        return {"error": "no shadow cycle yet", "live_trading": False}
    return result_report(result)


def replay_payload(cycle_id: str) -> dict[str, Any]:
    _ensure_loaded()
    return _safe(lambda: result_report(replay_cycle(cycle_id)))


def last_run_row() -> dict[str, str] | None:
    return last_experiment_row()


def halt_payload() -> dict[str, Any]:
    from quantlab.shadow.enums import KillReason

    halt(reason=KillReason.MANUAL_HALT)
    return {"mode": mode().value, "live_trading": False, "note": "HALT is not AUTO-LIQUIDATE"}


# Imported by tests that want a direct cycle without ledger.
def run_cycle_payload() -> dict[str, Any]:
    return result_report(run_shadow_cycle())
