"""Ops checkpoints. Hash mismatch is STATE_CORRUPT."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from quantlab.data.fabric.checksums import sha256_bytes
from quantlab.ops.errors import OpsError


class OpsCheckpoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    checkpoint_id: str
    payload_hash: str
    state: str


def write(path: Path, *, checkpoint_id: str, payload: str, state: str) -> OpsCheckpoint:
    digest = sha256_bytes(payload.encode())
    item = OpsCheckpoint(checkpoint_id=checkpoint_id, payload_hash=digest, state=state)
    path.write_text(item.model_dump_json())
    return item


def load(path: Path, *, expected_hash: str) -> OpsCheckpoint:
    item = OpsCheckpoint.model_validate_json(path.read_text())
    if item.payload_hash != expected_hash:
        raise OpsError("state checkpoint mismatch")
    return item
