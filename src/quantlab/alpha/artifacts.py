"""Feature/alpha experiment artifacts. Does not require a backtest equity curve."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantlab.domain.models import ExperimentRun


def write_feature_artifacts(root: Path, run: ExperimentRun, extra: dict[str, Any]) -> Path:
    folder = root / run.id
    folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "config": {
            "experiment_id": run.id,
            "config_hash": run.config_hash,
            "dataset_id": run.dataset_id,
            "dataset_version": run.dataset_version,
            "snapshot_id": run.snapshot_id,
            "feature_id": run.feature_id,
            "feature_version": run.feature_version,
            "label_definition": run.label_definition,
            "hyperparameters": run.hyperparameters,
            "data_kind": run.data_kind,
            "seed": run.random_seed,
        },
        "feature_definition": extra.get("feature_definition", {}),
        "label_definition": extra.get("label_definition", {}),
        "feature_quality": extra.get("quality", {}),
        "ic": extra.get("ic", {}),
        "quantiles": extra.get("quantiles", {}),
        "decay": extra.get("decay", {}),
        "correlations": extra.get("correlations", {}),
        "validation": extra.get("validation", {"note": "Prompt 05 suite not run in this path"}),
        "integrity": run.integrity,
        "lineage": run.lineage,
    }
    for name, body in payload.items():
        (folder / f"{name}.json").write_text(
            json.dumps(body, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
    return folder
