"""Restore requires a verified backup. No silent data loss."""

from __future__ import annotations

from pathlib import Path

from quantlab.ops.backup import get
from quantlab.ops.errors import BackupError


def restore(backup_id: str, dest: Path, *, require_verified: bool = True) -> Path:
    record = get(backup_id)
    if require_verified and not record.verified:
        raise BackupError("restore requires validation")
    if not record.recovery_ready:
        raise BackupError("unverified backup cannot be marked recovery-ready")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(Path(record.path).read_bytes())
    return dest
