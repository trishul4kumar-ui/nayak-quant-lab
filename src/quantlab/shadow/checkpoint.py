"""JSON sidecar checkpoints. Corrupt files fail closed."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from quantlab.core.config import get_settings
from quantlab.core.errors import CheckpointError
from quantlab.shadow.identity import hash_checkpoint
from quantlab.shadow.models import ShadowCheckpoint, ShadowResult


def default_path() -> Path:
    return Path(get_settings().experiment_ledger_path).with_name("shadow_checkpoint.json")


def build_checkpoint(result: ShadowResult, *, when: datetime) -> ShadowCheckpoint:
    item = ShadowCheckpoint(
        checkpoint_id=f"CHK-{result.cycle.cycle_id}",
        cycle_id=result.cycle.cycle_id,
        payload_hash="",
        portfolio_hash=result.portfolio.account_id,
        paper_account_id=result.paper_account.account_id,
        last_market_timestamp=result.freshness.data_timestamp,
        created_at=when,
    )
    return item.model_copy(update={"payload_hash": hash_checkpoint(item)})


def write_checkpoint(result: ShadowResult, path: Path | None = None) -> ShadowCheckpoint:
    target = path or default_path()
    checkpoint = result.checkpoint
    if checkpoint is None:
        raise CheckpointError("cannot persist a cycle without a checkpoint")
    payload = {
        "checkpoint": checkpoint.model_dump(mode="json"),
        "cycle_id": result.cycle.cycle_id,
        "result": result.model_dump(mode="json"),
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    return checkpoint


def read_checkpoint(path: Path | None = None) -> tuple[ShadowCheckpoint, ShadowResult]:
    target = path or default_path()
    if not target.exists():
        raise CheckpointError("checkpoint file is missing")
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        checkpoint = ShadowCheckpoint.model_validate(payload["checkpoint"])
        result = ShadowResult.model_validate(payload["result"])
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        raise CheckpointError("corrupt checkpoint") from exc
    expected = hash_checkpoint(checkpoint.model_copy(update={"payload_hash": ""}))
    if expected != checkpoint.payload_hash:
        raise CheckpointError("checkpoint_hash_mismatch")
    return checkpoint, result
