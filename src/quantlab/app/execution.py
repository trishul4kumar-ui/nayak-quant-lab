"""App-layer execution-research services. CLI and desktop call these, not the package internals."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantlab.core.config import get_settings
from quantlab.data.fabric.layout import resolve_fabric_root
from quantlab.execution_research.experiment import (
    ExecutionExperimentReport,
    run_named_execution_experiment,
)
from quantlab.execution_research.registry import get_execution_model, list_execution_models
from quantlab.models.registry import ExperimentLedger


def list_execution_model_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in list_execution_models():
        rows.append(
            {
                "definition_id": item.definition_id,
                "version": item.version,
                "name": item.name,
                "spread_model": item.spread_model.value,
                "slippage_model": item.slippage_model.value,
                "impact_model": item.impact_model.value,
                "latency_sessions": item.latency_sessions,
                "max_participation": item.max_participation,
                "identity": item.identity_hash(),
                "notes": item.notes,
            }
        )
    return rows


def inspect_execution_model(model_id: str) -> dict[str, Any]:
    model = get_execution_model(model_id)
    payload = model.model_dump(mode="json")
    payload["identity_hash"] = model.identity_hash()
    payload["note"] = (
        "Prompt 13 execution research. Distinct from quantlab.execution OMS. "
        "Simulated fills are not broker fills."
    )
    return payload


def simulate_execution_experiment(
    model_id: str,
    *,
    ledger: str = "",
    n_days: int = 80,
    family_size: int = 1,
    capital: float = 1_000_000.0,
    scenario_id: str | None = None,
    append: bool = True,
) -> tuple[ExecutionExperimentReport, dict[str, Any]]:
    report, run, sim = run_named_execution_experiment(
        model_id,
        ledger_path=_ledger_path(ledger),
        n_days=n_days,
        family_size=family_size,
        fabric_root=resolve_fabric_root(),
        append=append,
        capital=capital,
        scenario_id=scenario_id,
    )
    return report, {
        "experiment_id": run.id,
        "execution_model_id": report.execution_model_id,
        "identity_hash": report.identity_hash,
        "scenario_id": report.scenario_id,
        "gate_outcome": report.gate.outcome.value,
        "data_kind": report.data_kind,
        "gross_return": report.gross_return,
        "net_return": report.net_return,
        "total_cost": sim.total_cost,
        "mean_fill_ratio": sim.mean_fill_ratio,
        "n_fills": sim.n_fills,
        "n_partial": sim.n_partial,
        "fragility": report.fragility_score,
        "integrity": report.integrity,
        "note": report.note,
        "live_trading": False,
    }


def execution_report(experiment_id: str, *, ledger: str = "") -> dict[str, Any] | None:
    run = ExperimentLedger(_ledger_path(ledger)).get(experiment_id)
    if run is None:
        return None
    return {
        "experiment_id": run.id,
        "execution_model_id": run.execution_model_id,
        "execution_model_version": run.execution_model_version,
        "scenario_id": run.scenario_id,
        "scenario_version": run.scenario_version,
        "gate_outcome": run.gate_outcome,
        "data_kind": run.data_kind,
        "metrics": run.metrics,
        "integrity": run.integrity,
        "config_hash": run.config_hash,
        "random_seed": run.random_seed,
        "snapshot_id": run.snapshot_id,
        "dataset_id": run.dataset_id,
        "strategy_id": run.strategy_id,
    }


def _ledger_path(raw: str) -> Path:
    if raw:
        return Path(raw)
    return Path(get_settings().experiment_ledger_path)
