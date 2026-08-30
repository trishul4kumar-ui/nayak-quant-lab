from pathlib import Path

from quantlab.data.fabric.ingest import ingest_bars
from quantlab.data.fabric.layout import FabricLayout
from quantlab.data.fabric.quality import assess_bars
from quantlab.data.fabric.store import parquet_files
from quantlab.data.fabric.types import DataKind, DatasetState
from tests.data.helpers import make_bar, utc_day


def test_duplicates_are_quarantined_and_not_written_to_pit(tmp_path: Path) -> None:
    layout = FabricLayout(tmp_path)
    t0 = utc_day(2024, 1, 2)
    t1 = utc_day(2024, 1, 3)
    good = make_bar("TCS", t0, close=100.0)
    duplicate = make_bar("TCS", t0, close=101.0)
    later = make_bar("TCS", t1, close=102.0)
    accepted, report = assess_bars([good, duplicate, later])
    assert report.duplicate_count == 1
    assert len(accepted) == 2
    result = ingest_bars(
        layout,
        [good, duplicate, later],
        dataset_id="dupes",
        version="v1",
        source="test",
        data_kind=DataKind.SYNTHETIC,
        raw_name="bars.csv",
        raw_bytes=b"duplicate-rows",
        calendar_version="weekday-v1",
    )
    assert result.record.state is DatasetState.QUARANTINED
    assert parquet_files(layout, "dupes", "v1") == []
    quarantine = layout.quarantine_dir("dupes", "v1") / "rejects.jsonl"
    assert quarantine.exists()
    assert "duplicate" in quarantine.read_text(encoding="utf-8")


def test_file_on_disk_is_not_research_ready_without_gate(tmp_path: Path) -> None:
    layout = FabricLayout(tmp_path)
    layout.ensure()
    raw = layout.raw_dir("orphan", "v1") / "nse.csv"
    raw.write_text("symbol,date,open,high,low,close\nTCS,2024-01-02,1,1,1,1\n", encoding="utf-8")
    from quantlab.data.fabric.catalog import DatasetCatalog

    catalog = DatasetCatalog(layout)
    try:
        assert catalog.get("orphan", "v1") is None
    finally:
        catalog.close()
