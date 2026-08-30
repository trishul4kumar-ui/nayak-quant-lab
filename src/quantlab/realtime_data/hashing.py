"""Deterministic hashes for frozen observations and snapshots."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any


def iso(value: datetime) -> str:
    return value.isoformat()


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def sha256(payload: dict[str, Any] | str) -> str:
    text = payload if isinstance(payload, str) else canonical_json(payload)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
