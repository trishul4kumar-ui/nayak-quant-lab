"""App-layer econometrics. Qt does not fit models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from quantlab.core.config import get_settings
from quantlab.econometrics.experiment import run_econometrics_experiment
from quantlab.econometrics.models import EconometricRequest, EconometricResult
from quantlab.econometrics.reporting import result_report
from quantlab.econometrics.state import get_result, last_result, list_runs


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _ledger_path(raw: str) -> Path:
    if raw:
        return Path(raw)
    return Path(get_settings().experiment_ledger_path)


def list_payload() -> list[dict[str, Any]]:
    rows = [
        {
            "econometrics_run_id": item.run.econometrics_run_id,
            "spec_id": item.spec.spec_id,
            "claim": (
                None
                if item.diagnostics.causality is None
                else item.diagnostics.causality.claim.value
            ),
            "live_trading": False,
        }
        for item in list_runs()
    ]
    if not rows:
        rows.append(
            {
                "note": "No econometric runs. quantlab econometrics stationarity",
                "live_trading": False,
            }
        )
    return rows


def inspect_payload(run_id: str) -> dict[str, Any]:
    result = get_result(run_id)
    if result is None:
        return {"error": "no econometric run yet"}
    payload = _dump(result.run)
    payload["live_trading"] = False
    payload["note"] = "Inspect. Granger is predictive, not causation."
    return payload


def run_payload(*, ledger: str = "") -> dict[str, Any]:
    result, row = run_econometrics_experiment(
        EconometricRequest(),
        ledger_path=_ledger_path(ledger),
    )
    try:
        from quantlab.knowledge.ingest import persist_econometrics

        persist_econometrics(result, _ledger_path(ledger))
    except Exception:
        pass
    payload = result_report(result)
    payload["ledger_id"] = row.id
    return payload


def _need() -> EconometricResult:
    result = last_result()
    if result is None:
        run_payload()
        result = last_result()
    assert result is not None
    return result


def stationarity_payload() -> dict[str, Any]:
    result = _need()
    return {
        "tests": [_dump(item) for item in result.diagnostics.stationarity],
        "live_trading": False,
        "note": "Synthetic diagnostic. Not NSE evidence.",
    }


def dependence_payload() -> dict[str, Any]:
    dep = _need().diagnostics.dependence
    return {"missing": True} if dep is None else _dump(dep)


def cointegration_payload() -> dict[str, Any]:
    item = _need().diagnostics.cointegration
    return {"missing": True} if item is None else _dump(item)


def var_payload() -> dict[str, Any]:
    item = _need().var
    return {"missing": True} if item is None else _dump(item)


def vecm_payload() -> dict[str, Any]:
    item = _need().vecm
    return {"missing": True} if item is None else _dump(item)


def granger_payload() -> dict[str, Any]:
    item = _need().diagnostics.causality
    return {"missing": True} if item is None else _dump(item)


def breaks_payload() -> dict[str, Any]:
    item = _need().diagnostics.breaks
    return {"missing": True} if item is None else _dump(item)


def panel_payload() -> dict[str, Any]:
    item = _need().panel
    return {"missing": True} if item is None else _dump(item)


def causal_payload() -> dict[str, Any]:
    item = _need().causal
    return {"missing": True} if item is None else _dump(item)


def residuals_payload() -> dict[str, Any]:
    return {"n": len(_need().diagnostics.residuals), "live_trading": False}


def robustness_payload() -> dict[str, Any]:
    econ = _need().economics
    return {"missing": True} if econ is None else _dump(econ)


def report_payload() -> dict[str, Any]:
    return result_report(_need())


def last_run_row() -> dict[str, Any] | None:
    result = last_result()
    if result is None:
        return None
    return {
        "id": result.run.econometrics_run_id,
        "claim": (
            None
            if result.diagnostics.causality is None
            else result.diagnostics.causality.claim.value
        ),
        "family": result.multiple_testing.get("family_id", ""),
        "hash": result.run.run_hash,
    }
