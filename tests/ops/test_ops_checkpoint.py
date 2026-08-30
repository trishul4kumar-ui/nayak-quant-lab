from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.ops.checkpoints import load, write
from quantlab.ops.errors import OpsError


def test_state_checkpoint_mismatch_is_detected(tmp_path: Path) -> None:
    path = tmp_path / "ckpt.json"
    item = write(path, checkpoint_id="c1", payload="running", state="running")
    with pytest.raises(OpsError):
        load(path, expected_hash="not-the-hash")
    loaded = load(path, expected_hash=item.payload_hash)
    assert loaded.checkpoint_id == "c1"
