"""Cache identity includes snapshot, window, and seed."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.ensemble.cache import ensemble_cache_key
from quantlab.ensemble.registry import get_ensemble


@pytest.mark.ensemble
def test_cache_key_changes_with_snapshot() -> None:
    definition = get_ensemble("ew_mom_5_20")
    start = datetime(2024, 1, 2, tzinfo=UTC)
    left = ensemble_cache_key(
        definition,
        snapshot_id="a",
        universe=["NSE:TCS"],
        start=start,
        end=None,
        seed=0,
    )
    right = ensemble_cache_key(
        definition,
        snapshot_id="b",
        universe=["NSE:TCS"],
        start=start,
        end=None,
        seed=0,
    )
    assert left != right
