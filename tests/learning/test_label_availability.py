from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quantlab.core.errors import ModelError
from quantlab.labels.definition import resolve_label
from quantlab.learning.dataset import ModelDataset, labeled_rows


def test_declared_target_resolves_to_its_exact_definition() -> None:
    label = resolve_label("forward_return_5")
    assert label.label_id == "forward_return_5"
    assert label.horizon == 5


def test_delayed_label_is_excluded_before_its_available_time() -> None:
    decision_time = datetime(2026, 1, 2, tzinfo=UTC)
    cutoff = decision_time + timedelta(days=1)
    dataset = ModelDataset(
        dates=[decision_time],
        feature_ids=["feature"],
        features={"feature": {decision_time: {"NSE:ABC": 1.0}}},
        labels={decision_time: {"NSE:ABC": 0.2}},
        label_available_at={decision_time: {"NSE:ABC": decision_time + timedelta(days=2)}},
        label_id="forward_return_1",
    )

    with pytest.raises(ModelError, match="no labeled training rows"):
        labeled_rows(dataset, [decision_time], training_cutoff=cutoff)
