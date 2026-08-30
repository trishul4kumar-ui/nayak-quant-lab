from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from quantlab.ops.backup import create, verify
from quantlab.ops.clock import observe, reset_for_tests
from quantlab.ops.errors import BackupError, ClockError, OpsError
from quantlab.ops.resources import assert_disk, inject_free_bytes


def test_failure_injection(tmp_path: Path) -> None:
    inject_free_bytes(0)
    with pytest.raises(OpsError):
        assert_disk(min_free=1)
    reset_for_tests()
    with pytest.raises(ClockError):
        observe(datetime(1999, 1, 1, tzinfo=UTC))
    source = tmp_path / "ledger.jsonl"
    source.write_text("ok")
    record = create(source, tmp_path / "bak")
    Path(record.path).write_text("bad")
    with pytest.raises(BackupError):
        verify(record.backup_id)
