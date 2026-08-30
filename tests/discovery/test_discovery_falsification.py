from __future__ import annotations

import random
from datetime import UTC, datetime

import pytest

from quantlab.discovery.falsification import falsify_panel


@pytest.mark.discovery
def test_constant_null_is_weak() -> None:
    ts = [datetime(2024, 1, d, tzinfo=UTC) for d in range(2, 20)]
    panel = {t: {"A": 1.0, "B": 2.0, "C": 3.0, "D": 4.0} for t in ts}
    label = {t: {"A": 0.1, "B": -0.2, "C": 0.05, "D": 0.0} for t in ts}
    report = falsify_panel(panel, label, ts, random.Random(1))
    assert report.null_constant_ic is None or abs(report.null_constant_ic) < 0.2
    assert report.sign_reversal_ic is not None
