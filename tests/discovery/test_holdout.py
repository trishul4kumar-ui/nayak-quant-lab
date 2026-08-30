from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quantlab.discovery.validation import split_dates


@pytest.mark.discovery
def test_holdout_is_disjoint() -> None:
    dates = [datetime(2024, 1, 1, tzinfo=UTC) + timedelta(days=i) for i in range(40)]
    splits = split_dates(dates)
    train, val, hold = set(splits.train), set(splits.validation), set(splits.holdout)
    assert train.isdisjoint(val)
    assert train.isdisjoint(hold)
    assert val.isdisjoint(hold)
    assert len(splits.train) >= 8
