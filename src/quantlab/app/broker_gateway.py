"""App-layer read-only broker gateway. Qt cannot place orders."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from quantlab.broker_gateway.models import InternalBooks, MockScenario
from quantlab.broker_gateway.service import (
    audit_history,
    connect,
    disconnect,
    health,
    incidents,
    inspect,
    last_reconciliation,
    last_snapshot,
    list_connections,
    matching_internal_books,
    place_order,
    profile,
    reconcile,
    snapshot,
)
from quantlab.core.errors import QuantLabError


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _safe(fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return fn()
    except QuantLabError as exc:
        return {
            "error": str(exc),
            "live_trading": False,
            "write_enabled": False,
            "read_only": True,
        }


def status_payload() -> dict[str, Any]:
    item = health()
    payload = _dump(item)
    payload["note"] = "BROKER_CONNECTED ≠ TRADING_AUTHORIZED"
    return payload


def list_payload() -> list[dict[str, Any]]:
    rows = [
        {
            "id": item.bundle_id,
            "adapter_id": item.adapter_id,
            "hash": item.payload_hash,
            "live_trading": False,
        }
        for item in list_connections()
    ]
    if not rows:
        rows.append({"note": "No broker snapshots.", "live_trading": False, "read_only": True})
    return rows


def inspect_payload(item_id: str = "last") -> dict[str, Any]:
    bundle = inspect(item_id)
    if bundle is None:
        return {"note": "No snapshot.", "live_trading": False, "read_only": True}
    return _dump(bundle)


def health_payload() -> dict[str, Any]:
    return status_payload()


def connect_payload(scenario: str = "normal", *, adapter: str = "mock") -> dict[str, Any]:
    if adapter == "kite":
        return _safe(lambda: _dump(connect(adapter_name="kite")))
    return _safe(lambda: _dump(connect(MockScenario(scenario), adapter_name="mock")))


def disconnect_payload() -> dict[str, Any]:
    return _dump(disconnect())


def account_payload() -> dict[str, Any]:
    bundle = last_snapshot() or snapshot()
    return _dump(bundle.account)


def profile_payload() -> dict[str, Any]:
    return _dump(profile())


def positions_payload() -> dict[str, Any]:
    bundle = last_snapshot() or snapshot()
    return {"positions": [_dump(item) for item in bundle.positions], "live_trading": False}


def holdings_payload() -> dict[str, Any]:
    bundle = last_snapshot() or snapshot()
    return {"holdings": [_dump(item) for item in bundle.holdings], "live_trading": False}


def margins_payload() -> dict[str, Any]:
    bundle = last_snapshot() or snapshot()
    return _dump(bundle.margins)


def orders_payload() -> dict[str, Any]:
    bundle = last_snapshot() or snapshot()
    return {
        "orders": [_dump(item) for item in bundle.orders],
        "read_only": True,
        "live_trading": False,
    }


def fills_payload() -> dict[str, Any]:
    bundle = last_snapshot() or snapshot()
    return {
        "fills": [_dump(item) for item in bundle.fills],
        "read_only": True,
        "live_trading": False,
    }


def trades_payload() -> dict[str, Any]:
    bundle = last_snapshot() or snapshot()
    return {
        "trades": [_dump(item) for item in bundle.trades],
        "read_only": True,
        "live_trading": False,
    }


def snapshot_payload() -> dict[str, Any]:
    return _dump(snapshot())


def reconcile_payload(*, aligned: bool = False) -> dict[str, Any]:
    books: InternalBooks | None = matching_internal_books() if aligned else None
    return _dump(reconcile(books))


def audit_payload() -> dict[str, Any]:
    return {"count": len(audit_history()), "live_trading": False, "read_only": True}


def incidents_payload() -> dict[str, Any]:
    return {"incidents": [_dump(item) for item in incidents()], "live_trading": False}


def mappings_payload() -> dict[str, Any]:
    bundle = last_snapshot() or snapshot()
    return {"mappings": [_dump(item) for item in bundle.mappings], "live_trading": False}


def write_payload() -> dict[str, Any]:
    def _attempt() -> dict[str, Any]:
        place_order()
        return {"ok": False, "live_trading": False}

    return _safe(_attempt)


def last_run_row() -> dict[str, Any] | None:
    bundle = last_snapshot()
    recon = last_reconciliation()
    if bundle is None:
        return None
    return {
        "id": bundle.bundle_id,
        "hash": bundle.payload_hash,
        "state": health().state,
        "recon": recon.status.value if recon is not None else "none",
        "read_only": True,
    }


def run_payload() -> dict[str, Any]:
    connect()
    return snapshot_payload()
