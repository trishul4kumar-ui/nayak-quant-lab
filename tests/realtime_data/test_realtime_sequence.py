from __future__ import annotations

import pytest

from quantlab.realtime_data.mock import seed_observations
from quantlab.realtime_data.models import SequenceKind
from quantlab.realtime_data.sequence import classify

pytestmark = pytest.mark.realtime_data


def test_sequence_n_to_n_plus_1_is_valid() -> None:
    rows = seed_observations()
    assert classify(None, rows[0]) is SequenceKind.VALID
    assert classify(rows[0], rows[1]) is SequenceKind.VALID


def test_gap_and_duplicate() -> None:
    from quantlab.realtime_data.mock import MockFeedScenario

    gap = seed_observations(MockFeedScenario.GAP)
    assert classify(gap[0], gap[1]) is SequenceKind.GAP
    dup = seed_observations(MockFeedScenario.DUPLICATE)
    assert classify(dup[0], dup[1]) is SequenceKind.DUPLICATE
    ooo = seed_observations(MockFeedScenario.OUT_OF_ORDER)
    assert classify(ooo[0], ooo[1]) is SequenceKind.OUT_OF_ORDER
