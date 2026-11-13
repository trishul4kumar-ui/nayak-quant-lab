"""Source/version integrity tests use synthetic fixtures, not market evidence."""

import subprocess
import sys
from pathlib import Path

import pytest

from quantlab.core.errors import DataIntegrityError
from quantlab.data.fabric.catalog import DatasetCatalog
from quantlab.data.fabric.csvio import bars_to_csv_bytes
from quantlab.data.fabric.gate import GateVerdict, apply_gate_state, evaluate_research_gate
from quantlab.data.fabric.ingest import ingest_bars, ingest_csv
from quantlab.data.fabric.layout import FabricLayout
from quantlab.data.fabric.quality import DataQualityReport
from quantlab.data.fabric.types import DataKind
from quantlab.domain.research import CheckResult
from tests.data.helpers import make_bar, utc_day


def _source(path: Path, price: float = 100.0) -> None:
    path.write_bytes(bars_to_csv_bytes([make_bar("TCS", utc_day(2024, 1, 2), close=price)]))


def test_same_version_cannot_replace_raw_data(tmp_path: Path) -> None:
    layout = FabricLayout(tmp_path / "fabric")
    source = tmp_path / "input.csv"
    _source(source)
    first = ingest_csv(source, layout, dataset_id="prices", version="v1")
    raw = layout.raw / "prices" / "v1" / source.name
    original = raw.read_bytes()
    _source(source, 200.0)
    with pytest.raises(DataIntegrityError, match="DATASET_VERSION_CONFLICT"):
        ingest_csv(source, layout, dataset_id="prices", version="v1")
    assert raw.read_bytes() == original
    with DatasetCatalog(layout) as catalog:
        assert catalog.get("prices", "v1") == first.record


def test_same_raw_bytes_cannot_bind_different_bars(tmp_path: Path) -> None:
    layout = FabricLayout(tmp_path / "fabric")
    first = make_bar("TCS", utc_day(2024, 1, 2), close=100.0)
    other = make_bar("TCS", utc_day(2024, 1, 2), close=200.0)
    kwargs = dict(
        dataset_id="prices", version="v1", source="fixture", data_kind=DataKind.SYNTHETIC,
        raw_name="source.csv", raw_bytes=b"same source bytes", calendar_version="weekday-v1",
    )
    original = ingest_bars(layout, [first], **kwargs)
    with pytest.raises(DataIntegrityError, match="DATASET_VERSION_CONFLICT"):
        ingest_bars(layout, [other], **kwargs)
    with DatasetCatalog(layout) as catalog:
        assert catalog.get("prices", "v1") == original.record


@pytest.mark.parametrize("value", ["", "..", ".", "../escape", "/absolute", "a\\b"])
@pytest.mark.parametrize("field", ["dataset_id", "version", "raw_name"])
def test_ingestion_rejects_path_traversal(tmp_path: Path, field: str, value: str) -> None:
    layout = FabricLayout(tmp_path / "fabric")
    bar = make_bar("TCS", utc_day(2024, 1, 2))
    kwargs = dict(
        dataset_id="prices", version="v1", source="fixture", data_kind=DataKind.SYNTHETIC,
        raw_name="source.csv", raw_bytes=b"fixture", calendar_version="weekday-v1",
    )
    kwargs[field] = value
    with pytest.raises(DataIntegrityError, match="single nonempty path component"):
        ingest_bars(layout, [bar], **kwargs)
    assert not layout.root.exists()


def test_ingestion_rejects_symlinked_dataset_outside_fabric(tmp_path: Path) -> None:
    layout = FabricLayout(tmp_path / "fabric")
    outside = tmp_path / "outside"
    outside.mkdir()
    layout.raw.mkdir(parents=True)
    (layout.raw / "prices").symlink_to(outside, target_is_directory=True)
    bar = make_bar("TCS", utc_day(2024, 1, 2))
    with pytest.raises(DataIntegrityError, match="resolves outside"):
        ingest_bars(
            layout, [bar], dataset_id="prices", version="v1", source="fixture",
            data_kind=DataKind.SYNTHETIC, raw_name="source.csv", raw_bytes=b"fixture",
            calendar_version="weekday-v1",
        )
    assert not list(outside.iterdir())


def test_same_bytes_do_not_alias_other_dataset_identity(tmp_path: Path) -> None:
    layout = FabricLayout(tmp_path / "fabric")
    source = tmp_path / "input.csv"
    _source(source)
    first = ingest_csv(source, layout, dataset_id="one", version="v1")
    second = ingest_csv(source, layout, dataset_id="two", version="v1")
    assert not second.skipped
    assert first.record.dataset_id == "one"
    assert second.record.dataset_id == "two"
    assert first.record.checksum == second.record.checksum


def test_date_only_repeat_preserves_existing_catalog_record(tmp_path: Path) -> None:
    layout = FabricLayout(tmp_path / "fabric")
    source = tmp_path / "input.csv"
    source.write_text(
        "symbol,date,open,high,low,close,volume\nTCS,2024-01-02,100,101,99,100,1000\n",
        encoding="utf-8",
    )
    first = ingest_csv(source, layout, dataset_id="prices", version="v1")
    second = ingest_csv(source, layout, dataset_id="prices", version="v1")
    assert second.skipped
    assert second.record == first.record
    with DatasetCatalog(layout) as catalog:
        assert catalog.get("prices", "v1") == first.record


def test_matching_version_does_not_hide_raw_tampering(tmp_path: Path) -> None:
    layout = FabricLayout(tmp_path / "fabric")
    source = tmp_path / "input.csv"
    _source(source)
    ingest_csv(source, layout, dataset_id="prices", version="v1")
    raw = layout.raw / "prices" / "v1" / source.name
    raw.write_bytes(b"tampered")
    with pytest.raises(DataIntegrityError, match="DATASET_SOURCE_MISMATCH"):
        ingest_csv(source, layout, dataset_id="prices", version="v1")
    assert raw.read_bytes() == b"tampered"


def test_same_bytes_cannot_relabel_data_kind(tmp_path: Path) -> None:
    layout = FabricLayout(tmp_path / "fabric")
    source = tmp_path / "input.csv"
    _source(source)
    ingest_csv(source, layout, dataset_id="prices", version="v1", data_kind=DataKind.SYNTHETIC)
    with pytest.raises(DataIntegrityError, match="DATASET_VERSION_CONFLICT"):
        ingest_csv(source, layout, dataset_id="prices", version="v1", data_kind=DataKind.REAL)


def test_unregistered_partial_raw_is_not_overwritten(tmp_path: Path) -> None:
    layout = FabricLayout(tmp_path / "fabric")
    source = tmp_path / "input.csv"
    _source(source)
    raw = layout.raw_dir("prices", "v1") / source.name
    raw.write_bytes(b"prior partial source")
    with pytest.raises(DataIntegrityError, match="DATASET_VERSION_INCOMPLETE"):
        ingest_csv(source, layout, dataset_id="prices", version="v1")
    assert raw.read_bytes() == b"prior partial source"


def test_gate_report_cannot_promote_another_version(tmp_path: Path) -> None:
    layout = FabricLayout(tmp_path / "fabric")
    source = tmp_path / "input.csv"
    _source(source)
    record = ingest_csv(source, layout, dataset_id="prices", version="v1").record
    report = evaluate_research_gate(
        record, quality=DataQualityReport(rows_ingested=1, rows_accepted=1), pit_verified=True
    )
    with pytest.raises(DataIntegrityError, match="does not match dataset identity"):
        apply_gate_state(record.model_copy(update={"version": "v2"}), report)


@pytest.mark.parametrize("fault", ["optional_only", "missing", "not_required", "duplicate"])
def test_incomplete_or_inconsistent_ready_report_is_rejected(tmp_path: Path, fault: str) -> None:
    layout = FabricLayout(tmp_path / "fabric")
    source = tmp_path / "input.csv"
    _source(source)
    record = ingest_csv(source, layout, dataset_id="prices", version="v1").record
    report = evaluate_research_gate(
        record, quality=DataQualityReport(rows_ingested=1, rows_accepted=1), pit_verified=True
    )
    checks = report.checks.copy()
    if fault == "optional_only":
        checks = [GateVerdict(name="irrelevant", required=False, result=CheckResult.PASS)]
    elif fault == "missing":
        checks = [check for check in checks if check.name != "pit_verified"]
    elif fault == "not_required":
        checks = [
            check.model_copy(update={"required": False}) if check.name == "pit_verified" else check
            for check in checks
        ]
    else:
        checks.append(checks[0])
    with pytest.raises(DataIntegrityError, match="inconsistent readiness"):
        apply_gate_state(record, report.model_copy(update={"checks": checks}))


def test_concurrent_processes_cannot_overwrite_one_version(tmp_path: Path) -> None:
    script = """
import sys, time
from pathlib import Path
from quantlab.core.errors import DataIntegrityError
from quantlab.data.fabric.csvio import bars_to_csv_bytes
from quantlab.data.fabric import ingest
from quantlab.data.fabric.layout import FabricLayout
from quantlab.data.fabric.types import DataKind
from tests.data.helpers import make_bar, utc_day

bar = make_bar("TCS", utc_day(2024, 1, 2), close=float(sys.argv[2]))
payload = bars_to_csv_bytes([bar])
original_probe = ingest._probe_pit
def slow_probe(store, bars):
    time.sleep(0.25)
    return original_probe(store, bars)
ingest._probe_pit = slow_probe
sys.stdin.read(1)
try:
    result = ingest.ingest_bars(FabricLayout(Path(sys.argv[1])), [bar], dataset_id="prices",
        version="v1", source="source", data_kind=DataKind.SYNTHETIC, raw_name="source.csv",
        raw_bytes=payload, calendar_version="weekday-v1")
    print("OK " + result.record.checksum)
except DataIntegrityError as exc:
    print("ERROR " + str(exc))
"""
    workers = [
        subprocess.Popen(
            [sys.executable, "-c", script, str(tmp_path / "fabric"), str(price)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for price in (100, 200)
    ]
    outputs = []
    try:
        for worker in workers:
            assert worker.stdin is not None
            worker.stdin.write("x")
            worker.stdin.flush()
        for worker in workers:
            out, err = worker.communicate(timeout=30)
            assert worker.returncode == 0, err
            outputs.append(out.strip())
    finally:
        for worker in workers:
            if worker.poll() is None:
                worker.kill()
                worker.wait()
    assert sum(output.startswith("OK ") for output in outputs) == 1
    assert sum("DATASET_VERSION_CONFLICT" in output for output in outputs) == 1
    layout = FabricLayout(tmp_path / "fabric")
    with DatasetCatalog(layout) as catalog:
        record = catalog.get("prices", "v1")
    assert record is not None
    from quantlab.data.fabric.checksums import sha256_file

    assert sha256_file(layout.raw / "prices" / "v1" / "source.csv") == record.checksum


def test_writer_lock_released_when_process_dies(tmp_path: Path) -> None:
    script = """
import sys, time
from pathlib import Path
from quantlab.data.fabric.ingest import _ingest_writer_lock
from quantlab.data.fabric.layout import FabricLayout
with _ingest_writer_lock(FabricLayout(Path(sys.argv[1]))):
    print("locked", flush=True)
    time.sleep(60)
"""
    layout = FabricLayout(tmp_path / "fabric")
    worker = subprocess.Popen(
        [sys.executable, "-c", script, str(layout.root)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert worker.stdout is not None
        assert worker.stdout.readline().strip() == "locked"
        worker.kill()
        worker.wait(timeout=10)
        source = tmp_path / "input.csv"
        _source(source)
        assert ingest_csv(source, layout, dataset_id="prices", version="v1").research_ready
    finally:
        if worker.poll() is None:
            worker.kill()
            worker.wait()
