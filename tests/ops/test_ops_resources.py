from __future__ import annotations

import pytest

from quantlab.ops.errors import OpsError
from quantlab.ops.resources import assert_disk, inject_free_bytes


def test_disk_critical_state_is_detected() -> None:
    inject_free_bytes(1)
    with pytest.raises(OpsError):
        assert_disk(min_free=10_000_000)
