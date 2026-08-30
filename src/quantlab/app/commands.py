"""Application commands. UI must call these — never brokers or the firewall internals."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantlab.app.jobs import Job
from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import SafetyError
from quantlab.research.pipeline import run_momentum_validation, run_momentum_vertical_slice


def execute_momentum_backtest(job: Job, ledger_path: Path) -> dict[str, Any]:
    """Worker entry. Runs the real Prompt 02 slice. Not a screenshot fake."""
    if job.cancel_event.is_set():
        return {}
    params = job.parameters
    cost_bps = float(params.get("cost_bps", 10.0))
    if cost_bps <= 0:
        raise ValueError("cost_bps must be > 0")
    job.progress = 0.2
    result, run = run_momentum_vertical_slice(
        ledger_path=ledger_path,
        n_days=int(params.get("n_days", 80)),
        lookback=int(params.get("lookback", 20)),
        top_n=int(params.get("top_n", 2)),
        cost_bps=cost_bps,
        fabric_root=Path(params["fabric_root"]) if params.get("fabric_root") else None,
    )
    job.progress = 0.9
    return {
        "experiment_id": run.id,
        "hypothesis_id": run.hypothesis_id,
        "alpha_id": run.alpha_id,
        "genome_id": run.genome_id,
        "status": run.status.value,
        "total_return": result.total_return,
        "max_drawdown": result.max_drawdown,
        "n_rebalances": result.n_rebalances,
        "cost_drag": result.cost_drag,
        "metrics": result.metrics,
        "integrity": result.integrity,
        "equity_curve": result.equity_curve,
        "dates": [d.isoformat() for d in result.dates],
        "lineage": run.lineage,
        "application_version": run.application_version,
        "dataset_id": run.dataset_id,
        "data_kind": run.data_kind,
        "config_hash": run.config_hash,
        "live_trading": False,
        "conclusion": run.conclusion,
    }


def execute_momentum_validation(
    job: Job, ledger_path: Path, artifacts_dir: Path | None = None
) -> dict[str, Any]:
    if job.cancel_event.is_set():
        return {}
    params = job.parameters
    cost_bps = float(params.get("cost_bps", 10.0))
    if cost_bps <= 0:
        raise ValueError("cost_bps must be > 0")
    job.progress = 0.2
    result, run, report = run_momentum_validation(
        ledger_path=ledger_path,
        n_days=int(params.get("n_days", 80)),
        lookback=int(params.get("lookback", 20)),
        top_n=int(params.get("top_n", 2)),
        cost_bps=cost_bps,
        fabric_root=Path(params["fabric_root"]) if params.get("fabric_root") else None,
        artifacts_dir=artifacts_dir,
    )
    job.progress = 0.9
    return {
        "experiment_id": run.id,
        "status": run.status.value,
        "gate_outcome": run.gate_outcome,
        "gate_reasons": run.gate_reasons,
        "validation": run.validation,
        "metrics": result.metrics,
        "integrity": result.integrity,
        "equity_curve": result.equity_curve,
        "dates": [d.isoformat() for d in result.dates],
        "data_kind": run.data_kind,
        "config_hash": run.config_hash,
        "oos_windows": report.oos_windows,
        "oos_sharpe": report.oos_sharpe,
        "live_trading": False,
        "conclusion": run.conclusion,
    }


def request_live_trading(gates: LiveSafetyGates) -> None:
    """UI confirmation is not sufficient. Gates remain authoritative."""
    if not gates.all_pass():
        raise SafetyError("live trading blocked: " + ",".join(gates.blocking_reasons()))
    raise SafetyError("live broker path is not implemented")
