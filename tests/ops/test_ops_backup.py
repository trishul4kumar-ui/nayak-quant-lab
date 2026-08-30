from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.ops.backup import create, get, verify
from quantlab.ops.errors import BackupError


def test_corrupt_backup_fails_verification(tmp_path: Path) -> None:
    source = tmp_path / "ledger.jsonl"
    source.write_text("ok")
    record = create(source, tmp_path / "bak")
    Path(record.path).write_text("tampered")
    with pytest.raises(BackupError):
        verify(record.backup_id)


def test_unverified_backup_not_recovery_ready(tmp_path: Path) -> None:
    source = tmp_path / "ledger.jsonl"
    source.write_text("ok")
    record = create(source, tmp_path / "bak")
    assert record.verified is False
    assert record.recovery_ready is False
    assert get(record.backup_id).recovery_ready is False
