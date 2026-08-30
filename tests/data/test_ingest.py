from pathlib import Path

from quantlab.data.fabric.csvio import bars_to_csv_bytes
from quantlab.data.fabric.ingest import ingest_csv, materialize_synthetic
from quantlab.data.fabric.layout import FabricLayout
from quantlab.data.fabric.types import DataKind
from tests.data.helpers import make_bar, utc_day


def test_checksum_ingest_is_idempotent(tmp_path: Path) -> None:
    layout = FabricLayout(tmp_path)
    first = materialize_synthetic(layout, n_days=30)
    second = materialize_synthetic(layout, n_days=30)
    assert first.record.checksum == second.record.checksum
    assert second.skipped is True
    assert first.research_ready is True


def test_csv_ingest_path_labeled_synthetic(tmp_path: Path) -> None:
    layout = FabricLayout(tmp_path)
    bars = [
        make_bar("TCS", utc_day(2024, 1, 2), close=100.0),
        make_bar("TCS", utc_day(2024, 1, 3), close=101.0),
        make_bar("INFY", utc_day(2024, 1, 2), close=80.0),
        make_bar("INFY", utc_day(2024, 1, 3), close=81.0),
    ]
    csv_path = tmp_path / "user_nse.csv"
    csv_path.write_bytes(bars_to_csv_bytes(bars))
    result = ingest_csv(
        csv_path,
        layout,
        dataset_id="user-nse",
        version="v1",
        data_kind=DataKind.SYNTHETIC,
    )
    assert result.research_ready is True
    assert result.record.checksum
    assert result.record.source.endswith("user_nse.csv")
    again = ingest_csv(csv_path, layout, dataset_id="user-nse", version="v1")
    assert again.skipped is True
