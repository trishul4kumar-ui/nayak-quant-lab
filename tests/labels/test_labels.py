from datetime import UTC, datetime, timedelta

from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.domain.models import BarInterval, OHLCVBar
from quantlab.labels.definition import (
    forward_binary_direction,
    forward_excess_return,
    forward_return,
)
from quantlab.labels.engine import compute_label


def _series() -> list[OHLCVBar]:
    inst = InstrumentId.parse("NSE:TCS")
    start = datetime(2024, 1, 2, tzinfo=UTC)
    bars: list[OHLCVBar] = []
    price = 100.0
    for i in range(25):
        day = start + timedelta(days=i)
        if day.weekday() >= 5:
            continue
        price *= 1.01
        pit = PointInTime(
            event_time=day, effective_time=day, available_time=day, ingestion_time=day
        )
        bars.append(
            OHLCVBar(
                instrument=inst,
                pit=pit,
                interval=BarInterval.DAY,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=1_000,
            )
        )
    return bars


def test_forward_return_matches_hand_computation() -> None:
    series = _series()
    t = series[0].pit.event_time
    for horizon in (1, 5, 10):
        obs = compute_label(forward_return(horizon), series, t)
        expected = series[horizon].close / series[0].close - 1.0
        assert obs.value == expected
        assert obs.end_time is not None
        assert obs.end_time > t
        assert obs.available_time == obs.end_time


def test_binary_direction() -> None:
    series = _series()
    obs = compute_label(forward_binary_direction(1), series, series[0].pit.event_time)
    assert obs.value == 1.0


def test_excess_return_without_benchmark_is_not_tested() -> None:
    series = _series()
    obs = compute_label(forward_excess_return(1), series, series[0].pit.event_time)
    assert obs.value is None
    assert "NOT_TESTED" in obs.note
