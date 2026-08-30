from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quantlab.ops.clock import observe, reset_for_tests
from quantlab.ops.errors import ClockError


def test_clock_rollback_is_detected() -> None:
    reset_for_tests()
    observe(datetime(2024, 1, 2, tzinfo=UTC))
    with pytest.raises(ClockError):
        observe(datetime(2024, 1, 1, tzinfo=UTC))


def test_future_timestamps_are_rejected() -> None:
    reset_for_tests()
    with pytest.raises(ClockError):
        observe(datetime(2200, 1, 1, tzinfo=UTC) + timedelta(days=1))
