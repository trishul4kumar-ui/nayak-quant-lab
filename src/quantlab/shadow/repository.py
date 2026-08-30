"""JSON sidecar for shadow engine results. Not a second ledger."""

from __future__ import annotations

import json
from pathlib import Path

from quantlab.core.config import get_settings
from quantlab.shadow.state import last_result, list_results


def default_path() -> Path:
    return Path(get_settings().experiment_ledger_path).with_name("shadow_state.json")


def persist(path: Path | None = None) -> None:
    target = path or default_path()
    last = last_result()
    payload = {
        "last": last.cycle.cycle_id if last else None,
        "results": [item.model_dump(mode="json") for item in list_results()],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
