from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quantlab.discovery.validation import score_splits, split_dates
from quantlab.features.engine import Panel


@pytest.mark.discovery
def test_walk_forward_windows_on_train_only() -> None:
    dates = [datetime(2024, 1, 1, tzinfo=UTC) + timedelta(days=i) for i in range(40)]
    panel: Panel = {ts: {"A": float(i), "B": 1.0, "C": -float(i)} for i, ts in enumerate(dates)}
    label: Panel = {ts: {"A": float(i), "B": 0.5, "C": -float(i)} for i, ts in enumerate(dates)}
    splits = split_dates(dates)
    scores = score_splits(panel, label, splits)
    assert scores.walk_forward_windows >= 1
    assert scores.holdout_used_for_selection is False
    assert scores.train_ic is not None
