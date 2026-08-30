"""App-layer monitoring services. CLI and desktop call these. Qt does not attribute."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from quantlab.core.config import get_settings
from quantlab.monitoring.experiment import run_monitoring_experiment
from quantlab.monitoring.library import seed_paper_result
from quantlab.monitoring.models import MonitoringRequest, MonitoringResult
from quantlab.monitoring.reporting import result_report
from quantlab.monitoring.state import get_result, last_result, list_runs


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _ledger_path(raw: str) -> Path:
    if raw:
        return Path(raw)
    return Path(get_settings().experiment_ledger_path)


def list_payload() -> list[dict[str, Any]]:
    rows = []
    for item in list_runs():
        rows.append(
            {
                "monitoring_run_id": item.run.monitoring_run_id,
                "oms_run_id": item.run.oms_run_id,
                "pnl_total": item.pnl.pnl_total,
                "residual_pnl": item.pnl.residual_pnl,
                "live_trading": False,
                "note": "Monitoring observation. Not a claim.",
            }
        )
    if not rows:
        rows.append({"note": "No monitoring runs. quantlab monitor run", "live_trading": False})
    return rows


def inspect_payload(run_id: str) -> dict[str, Any]:
    result = get_result(run_id)
    if result is None:
        return {"error": "no monitoring run yet; run quantlab monitor run"}
    payload = _dump(result.run)
    payload["live_trading"] = False
    payload["note"] = "Inspect. Performance is not alpha."
    return payload


def run_payload(*, ledger: str = "") -> dict[str, Any]:
    paper, decision, target = seed_paper_result()
    result, row = run_monitoring_experiment(
        MonitoringRequest(),
        ledger_path=_ledger_path(ledger),
        paper=paper,
        decision=decision,
        target=target,
    )
    try:
        from quantlab.knowledge.ingest import persist_monitoring

        persist_monitoring(result, decision, _ledger_path(ledger))
    except Exception:
        pass
    payload = result_report(result)
    payload["ledger_id"] = row.id
    return payload


def _need() -> MonitoringResult:
    result = last_result()
    if result is None:
        run_payload()
        result = last_result()
    assert result is not None
    return result


def performance_payload() -> dict[str, Any]:
    return _dump(_need().snapshot)


def pnl_payload() -> dict[str, Any]:
    return _dump(_need().pnl)


def returns_payload() -> list[dict[str, Any]]:
    result = _need()
    return [_dump(item) for item in result.returns]


def attribution_payload() -> dict[str, Any]:
    return _dump(_need().attribution)


def factor_attribution_payload() -> dict[str, Any]:
    return _dump(_need().factor_attribution)


def alpha_attribution_payload() -> dict[str, Any]:
    return _dump(_need().alpha_attribution)


def exposure_payload() -> dict[str, Any]:
    return dict(_need().exposure)


def drift_payload() -> dict[str, Any]:
    return _dump(_need().drift)


def drawdown_payload() -> dict[str, Any]:
    return _dump(_need().drawdown)


def concentration_payload() -> dict[str, Any]:
    result = _need()
    return {"herfindahl": result.concentration, "live_trading": False}


def turnover_payload() -> dict[str, Any]:
    result = _need()
    return {"turnover": result.turnover, "live_trading": False}


def benchmark_payload() -> dict[str, Any]:
    return _dump(_need().benchmark)


def risk_payload() -> dict[str, Any]:
    return drawdown_payload()


def feedback_payload() -> list[dict[str, Any]]:
    result = _need()
    return [_dump(item) for item in result.feedback]


def reconcile_payload() -> dict[str, Any]:
    result = _need()
    return {
        "ok": result.reconciliation_ok,
        "pnl_identity": result.pnl.identity_ok,
        "residual_pnl": result.pnl.residual_pnl,
        "attribution_residual": result.attribution.residual,
        "live_trading": False,
    }


def report_payload() -> dict[str, Any]:
    result = _need()
    return result_report(result)


def last_run_row() -> dict[str, Any] | None:
    result = last_result()
    if result is None:
        return None
    return {
        "id": result.run.monitoring_run_id,
        "pnl": result.pnl.pnl_total,
        "residual": result.pnl.residual_pnl,
        "drift": result.drift.status.value,
        "hash": result.run.run_hash,
    }
