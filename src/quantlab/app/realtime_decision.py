"""App-layer real-time decision. Qt cannot place orders."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from quantlab.core.errors import QuantLabError
from quantlab.realtime_decision.models import (
    ActorKind,
    default_uncertified_release,
    synthetic_research_release,
)
from quantlab.realtime_decision.service import (
    audit_history,
    inspect,
    list_decisions,
    run_realtime_decision,
)
from quantlab.realtime_decision.state import current

_LAST: dict[str, Any] | None = None


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _safe(fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return fn()
    except QuantLabError as exc:
        return {
            "error": str(exc),
            "live_trading": False,
            "decision_is_not_order": True,
        }


def last_run_row() -> dict[str, Any] | None:
    return _LAST


def _store(row: dict[str, Any]) -> dict[str, Any]:
    global _LAST
    _LAST = row
    return row


def _release(kind: str, as_of: Any) -> Any:
    if kind == "research":
        return synthetic_research_release(as_of=as_of)
    return default_uncertified_release(as_of=as_of)


def status_payload() -> dict[str, Any]:
    last = inspect("last")
    return {
        "state": current().value,
        "decision_id": last.decision_id if last else "",
        "abstention": last.abstention.value if last else "",
        "live_trading": False,
        "note": "DECISION ≠ ORDER. LIVE DISABLED.",
    }


def releases_payload() -> dict[str, Any]:
    return {
        "releases": ["default-uncertified", "synthetic-research"],
        "never_implicit_latest": True,
        "live_trading": False,
    }


def inspect_payload(item_id: str = "last") -> dict[str, Any]:
    item = inspect(item_id)
    if item is None:
        return {"note": "No decision yet.", "live_trading": False}
    return _dump(item)


def run_payload(release: str = "default") -> dict[str, Any]:
    def _go() -> dict[str, Any]:
        from quantlab.realtime_data.mock import SEED_AS_OF

        bound = _release(release, SEED_AS_OF)
        item = run_realtime_decision(release=bound, actor=ActorKind.SYSTEM)
        return _store(
            {
                "id": item.decision_id,
                "hash": item.decision_hash,
                "state": item.state,
                "abstention": item.abstention.value,
                "portfolio": item.target.portfolio_hash if item.target else "",
                "live_trading": False,
                **_dump(item),
            }
        )

    return _safe(_go)


def explain_payload() -> dict[str, Any]:
    item = inspect("last")
    if item is None:
        return run_payload()
    return {
        "decision_id": item.decision_id,
        "cycle": list(item.cycle),
        "abstention": item.abstention.value,
        "note": item.note,
        "live_trading": False,
    }


def abstentions_payload() -> dict[str, Any]:
    item = inspect("last")
    return {
        "abstention": item.abstention.value if item else "none",
        "comfortable_with_no_decision": True,
        "live_trading": False,
    }


def risk_payload() -> dict[str, Any]:
    return {"risk": "composed Prompt 08; no bypass", "live_trading": False}


def exposure_payload() -> dict[str, Any]:
    item = inspect("last")
    if item is None or item.target is None:
        return {"gross_exposure": 0.0, "live_trading": False}
    return {
        "gross_exposure": item.target.gross_exposure,
        "net_exposure": item.target.net_exposure,
        "live_trading": False,
    }


def portfolio_payload() -> dict[str, Any]:
    item = inspect("last")
    if item is None or item.target is None:
        return {"note": "No target. Abstention is first-class.", "live_trading": False}
    return {**_dump(item.target), "not_an_order": True}


def replay_payload() -> dict[str, Any]:
    original = inspect("last")
    if original is None:
        return run_payload("research")
    from quantlab.realtime_data.service import inspect as inspect_snap

    snap = inspect_snap(original.snapshot_id)
    bound = (
        synthetic_research_release(as_of=original.as_of)
        if original.target is not None
        else default_uncertified_release(as_of=original.as_of)
    )
    replayed = run_realtime_decision(release=bound, frozen=snap)
    return {
        "original": original.decision_hash,
        "replay": replayed.decision_hash,
        "match": original.decision_hash == replayed.decision_hash,
        "live_trading": False,
    }


def audit_payload() -> list[dict[str, Any]]:
    return audit_history() or [{"note": "No decision audit yet.", "live_trading": False}]


def lineage_payload() -> dict[str, Any]:
    item = inspect("last")
    return {
        "lineage": [
            "snapshot",
            "feature",
            "alpha",
            "model",
            "ensemble",
            "portfolio",
            "capital",
            "risk",
            "decision",
        ],
        "decision_id": item.decision_id if item else "",
        "live_trading": False,
    }


def list_payload() -> list[dict[str, Any]]:
    ids = list_decisions()
    if not ids:
        return [{"note": "No decisions.", "live_trading": False}]
    return [{"id": item, "live_trading": False} for item in ids]
