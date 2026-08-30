from __future__ import annotations

import pytest

from quantlab.orchestration.errors import OrchestrationError
from quantlab.orchestration.snapshot import DatasetSnapshot, assert_same_snapshot


@pytest.mark.orchestration
def test_snapshot_pin_mismatch() -> None:
    a = DatasetSnapshot(
        dataset_id="synthetic_nse",
        dataset_version="1",
        snapshot_id="aaa",
        checksum="c1",
    )
    b = a.model_copy(update={"snapshot_id": "bbb"})
    with pytest.raises(OrchestrationError, match="snapshot"):
        assert_same_snapshot(a, b)
    assert_same_snapshot(a, a)
