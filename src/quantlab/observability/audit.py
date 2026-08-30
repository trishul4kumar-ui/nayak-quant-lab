"""Append-only audit records. Never log secrets."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class AuditLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event_type: str, component: str, metadata: dict[str, Any]) -> None:
        row = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "event_type": event_type,
            "component": component,
            "metadata": metadata,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
