"""JSON sidecar for certification results."""

from __future__ import annotations

import json
from pathlib import Path

from quantlab.certification.state import last_result, list_runs
from quantlab.core.config import get_settings


def default_path() -> Path:
    return Path(get_settings().experiment_ledger_path).with_name("certification_state.json")


def persist(path: Path | None = None) -> None:
    target = path or default_path()
    last = last_result()
    payload = {
        "last": None if last is None else last.run.certification_id,
        "results": [item.model_dump(mode="json") for item in list_runs()],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
