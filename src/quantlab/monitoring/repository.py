"""JSON sidecar for monitoring results. Not a second ledger."""

from __future__ import annotations

import json
from pathlib import Path

from quantlab.core.config import get_settings
from quantlab.monitoring.models import MonitoringResult
from quantlab.monitoring.state import get_result, last_result, list_runs


def default_path() -> Path:
    return Path(get_settings().experiment_ledger_path).with_name("monitoring_state.json")


def persist(path: Path | None = None) -> None:
    target = path or default_path()
    rows = [item.model_dump(mode="json") for item in list_runs()]
    last = last_result()
    payload = {
        "last": None if last is None else last.run.monitoring_run_id,
        "results": rows,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def load_one(run_id: str) -> MonitoringResult | None:
    return get_result(run_id)
