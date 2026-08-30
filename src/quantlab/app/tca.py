"""App-layer TCA services. Qt does not calibrate or route."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from quantlab.core.config import get_settings
from quantlab.tca.enums import TCAKind
from quantlab.tca.experiment import run_tca_experiment
from quantlab.tca.models import TCARequest, TCAResult
from quantlab.tca.state import get_result, last_result, list_runs
from quantlab.tca.uncertainty import interval


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _ledger_path(raw: str) -> Path:
    if raw:
        return Path(raw)
    return Path(get_settings().experiment_ledger_path)


def list_payload() -> list[dict[str, Any]]:
    rows = [
        {
            "tca_run_id": item.run.tca_run_id,
            "kind": item.kind.value,
            "shortfall": item.shortfall.total,
            "fragility": item.fragility.status.value,
            "live_trading": False,
        }
        for item in list_runs()
    ]
    if not rows:
        rows.append({"note": "No TCA runs. quantlab tca run", "live_trading": False})
    return rows


def inspect_payload(run_id: str) -> dict[str, Any]:
    result = get_result(run_id)
    if result is None:
        return {"error": "no TCA run yet; run quantlab tca run"}
    payload = _dump(result.run)
    payload["live_trading"] = False
    payload["note"] = "Inspect. Modelled is not observed."
    return payload


def run_payload(*, ledger: str = "", calibrate: bool = False) -> dict[str, Any]:
    result, row = run_tca_experiment(
        TCARequest(calibrate=calibrate),
        ledger_path=_ledger_path(ledger),
    )
    try:
        from quantlab.knowledge.ingest import persist_tca

        persist_tca(result, _ledger_path(ledger))
    except Exception:
        pass
    return {
        "tca_run_id": result.run.tca_run_id,
        "kind": result.kind.value,
        "shortfall": result.shortfall.total,
        "capacity": result.capacity.status.value,
        "fragility": result.fragility.status.value,
        "ledger_id": row.id,
        "live_trading": False,
        "note": result.note,
        "hash": result.run.tca_hash,
    }


def _need() -> TCAResult:
    result = last_result()
    if result is None:
        run_payload()
        result = last_result()
    assert result is not None
    return result


def spread_payload() -> dict[str, Any]:
    result = _need()
    return {"spread_kind": result.spread_kind.value, "note": result.note}


def slippage_payload() -> dict[str, Any]:
    result = _need()
    return {"trading_cost": result.shortfall.trading_cost, "live_trading": False}


def impact_payload() -> dict[str, Any]:
    result = _need()
    cal = result.calibration
    return {
        "market_impact": result.shortfall.market_impact,
        "estimate": None if cal is None else interval(cal.estimate, cal.uncertainty),
        "live_trading": False,
    }


def shortfall_payload() -> dict[str, Any]:
    result = _need()
    return _dump(result.shortfall)


def costs_payload() -> list[dict[str, Any]]:
    result = _need()
    return [_dump(item) for item in result.costs]


def latency_payload() -> dict[str, Any]:
    return {"delay_cost": _need().shortfall.delay_cost, "live_trading": False}


def liquidity_payload() -> dict[str, Any]:
    return _dump(_need().liquidity)


def calibrate_payload(*, ledger: str = "") -> dict[str, Any]:
    return run_payload(ledger=ledger, calibrate=True)


def calibration_report_payload() -> dict[str, Any]:
    result = _need()
    if result.calibration is None:
        return {"note": "No calibration. quantlab tca calibrate", "status": "NOT_TESTED"}
    return _dump(result.calibration)


def capacity_payload() -> dict[str, Any]:
    return _dump(_need().capacity)


def fragility_payload() -> dict[str, Any]:
    return _dump(_need().fragility)


def sensitivity_payload() -> dict[str, Any]:
    from quantlab.tca.sensitivity import scale_shortfall

    result = _need()
    return {
        "x1": scale_shortfall(result.shortfall, 1.0),
        "x2": scale_shortfall(result.shortfall, 2.0),
        "note": "Diagnostic multipliers. Not a gate.",
    }


def stress_payload() -> dict[str, Any]:
    result = _need()
    return {
        "kind": TCAKind.STRESSED.value,
        "stressed_shortfall": (result.shortfall.total or 0.0) * 2.0,
        "note": "STRESSED_TCA. Not observed.",
    }


def compare_payload() -> dict[str, Any]:
    return dict(_need().paper_comparison)


def report_payload() -> dict[str, Any]:
    result = _need()
    return {
        "tca_run_id": result.run.tca_run_id,
        "kind": result.kind.value,
        "shortfall": result.shortfall.total,
        "capacity": result.capacity.status.value,
        "fragility": result.fragility.status.value,
        "hash": result.run.tca_hash,
        "live_trading": False,
        "note": result.note,
    }


def last_run_row() -> dict[str, Any] | None:
    result = last_result()
    if result is None:
        return None
    return {
        "id": result.run.tca_run_id,
        "kind": result.kind.value,
        "shortfall": result.shortfall.total,
        "fragility": result.fragility.status.value,
        "hash": result.run.tca_hash,
    }
