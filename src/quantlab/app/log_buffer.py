"""In-process log ring buffer. Never stores secrets."""

from __future__ import annotations

import json
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any


class LogBuffer:
    def __init__(self, maxlen: int = 4000, log_file: Path | None = None) -> None:
        self._records: deque[dict[str, Any]] = deque(maxlen=maxlen)
        self._lock = Lock()
        self.log_file = log_file

    def append(self, record: dict[str, Any]) -> None:
        row = dict(record)
        row.setdefault("timestamp", datetime.now(tz=UTC).isoformat())
        with self._lock:
            self._records.append(row)
            if self.log_file is not None:
                with self.log_file.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(row, default=str) + "\n")

    def snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._records)

    def flush(self) -> None:
        return None
