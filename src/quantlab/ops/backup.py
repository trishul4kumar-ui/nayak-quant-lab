"""Checksummed backups. Unverified backups are not recovery-ready."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from quantlab.data.fabric.checksums import sha256_bytes, sha256_file
from quantlab.ops.errors import BackupError
from quantlab.ops.models import BackupRecord

_RECORDS: dict[str, BackupRecord] = {}


def reset_for_tests() -> None:
    _RECORDS.clear()


def create(source: Path, dest_dir: Path) -> BackupRecord:
    dest_dir.mkdir(parents=True, exist_ok=True)
    payload = source.read_bytes() if source.exists() else b""
    checksum = sha256_bytes(payload)
    dest = dest_dir / "ledger.jsonl"
    dest.write_bytes(payload)
    record = BackupRecord(
        backup_id=f"bak-{checksum[:12]}",
        path=str(dest),
        checksum=checksum,
        verified=False,
        created_at=datetime(2024, 1, 2, tzinfo=UTC),
        recovery_ready=False,
    )
    _RECORDS[record.backup_id] = record
    return record


def verify(backup_id: str) -> BackupRecord:
    record = _RECORDS[backup_id]
    path = Path(record.path)
    if not path.exists():
        raise BackupError("backup missing")
    digest = sha256_file(path)
    if digest != record.checksum:
        raise BackupError("backup checksum failure")
    updated = record.model_copy(update={"verified": True, "recovery_ready": True})
    _RECORDS[backup_id] = updated
    return updated


def get(backup_id: str) -> BackupRecord:
    return _RECORDS[backup_id]


def list_backups() -> list[BackupRecord]:
    return list(_RECORDS.values())
