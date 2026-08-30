from datetime import timedelta
from pathlib import Path

from quantlab.data.fabric.ingest import ingest_bars
from quantlab.data.fabric.layout import FabricLayout
from quantlab.data.fabric.store import PitStore
from quantlab.data.fabric.types import DataKind
from tests.data.helpers import make_bar, utc_day, weekday_series


def test_query_excludes_future_available_bars(tmp_path: Path) -> None:
    layout = FabricLayout(tmp_path)
    t0 = utc_day(2024, 1, 2)
    t1 = utc_day(2024, 1, 3)
    t2 = utc_day(2024, 1, 4)
    bars = [
        make_bar("TCS", t0, close=100.0),
        make_bar("TCS", t1, close=101.0),
        make_bar("TCS", t2, close=102.0, available=t2 + timedelta(days=5)),
    ]
    ingest_bars(
        layout,
        bars,
        dataset_id="pit-future",
        version="v1",
        source="test",
        data_kind=DataKind.SYNTHETIC,
        raw_name="bars.csv",
        raw_bytes=b"fixture",
        calendar_version="weekday-v1",
    )
    store = PitStore(layout, "pit-future", "v1")
    as_of = t1
    got = store.query(as_of=as_of)
    assert [b.close for b in got] == [100.0, 101.0]
    assert all(b.pit.available_time <= as_of for b in got)


def test_no_query_returns_available_after_as_of(tmp_path: Path) -> None:
    layout = FabricLayout(tmp_path)
    series = weekday_series("INFY", utc_day(2024, 1, 2), 15)
    delayed = weekday_series("TCS", utc_day(2024, 1, 2), 15, delay=timedelta(days=2))
    ingest_bars(
        layout,
        series + delayed,
        dataset_id="pit-property",
        version="v1",
        source="test",
        data_kind=DataKind.SYNTHETIC,
        raw_name="bars.csv",
        raw_bytes=b"fixture-property",
        calendar_version="weekday-v1",
    )
    store = PitStore(layout, "pit-property", "v1")
    times = [b.pit.available_time for b in series + delayed]
    sample = sorted(set(times))[::2]
    for as_of in sample:
        got = store.query(as_of=as_of)
        assert all(bar.pit.available_time <= as_of for bar in got)
