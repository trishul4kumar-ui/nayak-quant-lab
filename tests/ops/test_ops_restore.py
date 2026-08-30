from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.ops.backup import create
from quantlab.ops.errors import BackupError
from quantlab.ops.restore import restore


def test_restore_requires_validation(tmp_path: Path) -> None:
    source = tmp_path / "ledger.jsonl"
    source.write_text("ok")
    record = create(source, tmp_path / "bak")
    with pytest.raises(BackupError):
        restore(record.backup_id, tmp_path / "out.jsonl", require_verified=True)
