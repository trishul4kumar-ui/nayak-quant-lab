"""Explicit, size-bounded saved research input import; never substitutes mock data."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from quantlab.agents.context import FrozenHistory
from quantlab.agents.contracts import DataKind
from quantlab.domain.models import OHLCVBar
from quantlab.realtime_data.models import RealTimeSnapshot


def read_snapshot(path: Path) -> RealTimeSnapshot:
    if path.stat().st_size > 4_000_000:
        raise ValueError("SNAPSHOT_INPUT_TOO_LARGE")
    return RealTimeSnapshot.model_validate_json(path.read_bytes())


def read_history(path: Path, snapshot: RealTimeSnapshot, now: datetime) -> FrozenHistory:
    if path.stat().st_size > 12_000_000:
        raise ValueError("HISTORY_INPUT_TOO_LARGE")
    payload = json.loads(path.read_bytes())
    if not isinstance(payload, dict) or set(payload) != {"bars", "price_basis", "data_kind"}:
        raise ValueError("INVALID_HISTORY_INPUT")
    bars = payload["bars"]
    if not isinstance(bars, list) or len(bars) > 5040:
        raise ValueError("HISTORY_BUDGET_EXCEEDED")
    return FrozenHistory(
        created_at=now,
        snapshot_hash=snapshot.snapshot_hash,
        bars_json=tuple(OHLCVBar.model_validate(bar).model_dump_json() for bar in bars),
        price_basis=payload["price_basis"],
        data_kind=DataKind(payload["data_kind"]),
    )
