"""Machine-readable research artifacts. Ledger rows remain append-only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantlab.backtest.engine import BacktestResult
from quantlab.domain.models import ExperimentRun


def write_experiment_artifacts(
    root: Path,
    run: ExperimentRun,
    result: BacktestResult,
    extra: dict[str, Any],
) -> Path:
    folder = root / run.id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "config.json").write_text(
        json.dumps(
            {
                "experiment_id": run.id,
                "config_hash": run.config_hash,
                "dataset_id": run.dataset_id,
                "dataset_version": run.dataset_version,
                "snapshot_id": run.snapshot_id,
                "hyperparameters": run.hyperparameters,
                "data_kind": run.data_kind,
                "seed": run.random_seed,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (folder / "metrics.json").write_text(json.dumps(run.metrics, indent=2) + "\n", encoding="utf-8")
    (folder / "integrity.json").write_text(
        json.dumps(run.integrity, indent=2) + "\n", encoding="utf-8"
    )
    (folder / "lineage.json").write_text(json.dumps(run.lineage, indent=2) + "\n", encoding="utf-8")
    (folder / "validation.json").write_text(
        json.dumps(extra, indent=2, default=str) + "\n", encoding="utf-8"
    )
    equity = {
        "dates": [d.isoformat() for d in result.dates],
        "equity": result.equity_curve,
        "turnover": result.turnover,
    }
    (folder / "equity.json").write_text(json.dumps(equity, indent=2) + "\n", encoding="utf-8")
    return folder
