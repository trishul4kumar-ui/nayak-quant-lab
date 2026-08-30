"""Ingest: source → raw (immutable) + checksum → validate → Parquet → catalog."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as pq
from pydantic import BaseModel, Field

from quantlab.core.errors import DataIntegrityError
from quantlab.data.fabric.calendar import WeekdayCalendar, session_date_ist
from quantlab.data.fabric.catalog import DatasetCatalog, DatasetRecord
from quantlab.data.fabric.checksums import sha256_bytes, sha256_file
from quantlab.data.fabric.csvio import bars_to_csv_bytes, parse_ohlcv_csv
from quantlab.data.fabric.gate import apply_gate_state, evaluate_research_gate
from quantlab.data.fabric.layout import FabricLayout
from quantlab.data.fabric.quality import DataQualityReport, assess_bars
from quantlab.data.fabric.store import PitStore, bars_to_table, parquet_files
from quantlab.data.fabric.types import DataKind, DatasetState, PriceKind
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import OHLCVBar

SYNTHETIC_DATASET_ID = "synthetic-nse"
SYNTHETIC_VERSION = "synthetic-nse-v1"


class IngestResult(BaseModel):
    record: DatasetRecord
    skipped: bool = False
    quality: DataQualityReport = Field(default_factory=DataQualityReport)
    gate: dict[str, str] = Field(default_factory=dict)
    research_ready: bool = False
    rows_written: int = 0
    availability_convention: str = "explicit"


def stamp_bars(
    bars: list[OHLCVBar],
    *,
    dataset_version: str,
    source_id: str,
    data_kind: DataKind,
) -> list[OHLCVBar]:
    stamped: list[OHLCVBar] = []
    for bar in bars:
        stamped.append(
            bar.model_copy(
                update={
                    "dataset_version": dataset_version,
                    "source_id": source_id,
                    "session_date": bar.session_date
                    or session_date_ist(bar.pit.event_time).isoformat(),
                    "price_kind": bar.price_kind or PriceKind.RAW_PRICE.value,
                    "data_kind": data_kind.value,
                }
            )
        )
    return stamped


def _write_sidecar(path: Path, payload: dict[str, str]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_quarantine(
    layout: FabricLayout, dataset_id: str, version: str, report: DataQualityReport
) -> None:
    if not report.quarantine:
        return
    dest = layout.quarantine_dir(dataset_id, version) / "rejects.jsonl"
    with dest.open("w", encoding="utf-8") as handle:
        for item in report.quarantine:
            handle.write(item.model_dump_json() + "\n")


def _probe_pit(store: PitStore, bars: list[OHLCVBar]) -> bool:
    latest = max(bar.pit.available_time for bar in bars)
    early = min(bar.pit.available_time for bar in bars)
    full = store.query(as_of=latest)
    if any(bar.pit.available_time > latest for bar in full):
        return False
    early_rows = store.query(as_of=early)
    return all(bar.pit.available_time <= early for bar in early_rows)


def ingest_bars(
    layout: FabricLayout,
    bars: list[OHLCVBar],
    *,
    dataset_id: str,
    version: str,
    source: str,
    data_kind: DataKind,
    raw_name: str,
    raw_bytes: bytes,
    calendar_version: str,
    availability_convention: str = "explicit",
    corporate_action_policy: str = "none",
    universe_version: str = "",
) -> IngestResult:
    layout.ensure()
    checksum = sha256_bytes(raw_bytes)
    catalog = DatasetCatalog(layout)
    try:
        existing = catalog.find_by_checksum(checksum)
        if (
            existing is not None
            and existing.dataset_id == dataset_id
            and existing.version == version
            and existing.state is DatasetState.RESEARCH_READY
            and parquet_files(layout, dataset_id, version)
        ):
            return IngestResult(
                record=existing,
                skipped=True,
                research_ready=True,
                availability_convention=existing.extra.get(
                    "availability_convention", availability_convention
                ),
            )

        raw_dir = layout.raw_dir(dataset_id, version)
        dest = raw_dir / raw_name
        dest.write_bytes(raw_bytes)
        _write_sidecar(
            raw_dir / f"{raw_name}.sidecar.json",
            {
                "checksum": checksum,
                "original_filename": raw_name,
                "retrieved_at": datetime.now(tz=UTC).isoformat(),
                "schema": "ohlcv_csv_v1",
                "source": source,
                "data_kind": data_kind.value,
                "availability_convention": availability_convention,
            },
        )

        accepted, quality = assess_bars(bars)
        _write_quarantine(layout, dataset_id, version, quality)
        snapshot_id = checksum[:16]
        if accepted:
            table = bars_to_table(accepted)
            pq.write_table(table, layout.normalized_dir(dataset_id, version) / "bars.parquet")

        contaminated = quality.invalid_count > 0 or quality.duplicate_count > 0
        record = DatasetRecord(
            dataset_id=dataset_id,
            version=version,
            state=DatasetState.QUARANTINED
            if contaminated or not accepted
            else DatasetState.CURATED,
            data_kind=data_kind,
            source=source,
            checksum=checksum,
            schema_name="ohlcv_csv_v1",
            coverage=f"rows={quality.rows_accepted} instruments={quality.instrument_count}",
            price_adjustment_method=PriceKind.RAW_PRICE.value,
            corporate_action_policy=corporate_action_policy,
            calendar_version=calendar_version,
            universe_version=universe_version,
            snapshot_id=snapshot_id,
            notes=(
                "weekday calendar is not an official NSE holiday file"
                if calendar_version.startswith("weekday")
                else ""
            ),
            extra={
                "availability_convention": availability_convention,
                "raw_filename": raw_name,
                "max_available_time": (
                    max(b.pit.available_time for b in accepted).isoformat() if accepted else ""
                ),
            },
        )

        pit_ok: bool | None = None
        rows_written = 0
        if accepted and not contaminated:
            pq.write_table(table, layout.curated_dir(dataset_id, version) / "bars.parquet")
            store = PitStore(layout, dataset_id, version)
            store.write_bars(accepted)
            rows_written = len(accepted)
            pit_ok = _probe_pit(store, accepted)
            if not pit_ok:
                record = record.model_copy(update={"state": DatasetState.QUARANTINED})

        gate = evaluate_research_gate(
            record,
            quality=quality,
            pit_verified=pit_ok,
            timezone_defined=True,
            identity_present=True,
        )
        if record.state is not DatasetState.QUARANTINED:
            record = apply_gate_state(record, gate)
        catalog.upsert(record)
        return IngestResult(
            record=record,
            skipped=False,
            quality=quality,
            gate=gate.as_str_map(),
            research_ready=gate.research_ready and record.state is DatasetState.RESEARCH_READY,
            rows_written=rows_written,
            availability_convention=availability_convention,
        )
    finally:
        catalog.close()


def ingest_csv(
    source: Path,
    layout: FabricLayout,
    *,
    dataset_id: str,
    version: str,
    data_kind: DataKind = DataKind.REAL,
    calendar: WeekdayCalendar | None = None,
) -> IngestResult:
    if not source.is_file():
        raise DataIntegrityError(f"ingest source is not a file: {source}")
    calendar = calendar or WeekdayCalendar()
    checksum = sha256_file(source)
    catalog = DatasetCatalog(layout)
    try:
        existing = catalog.find_by_checksum(checksum)
        if existing is not None and existing.state is DatasetState.RESEARCH_READY:
            pit_files = list(
                layout.pit_dir(existing.dataset_id, existing.version).glob("year=*/bars.parquet")
            )
            if pit_files:
                return IngestResult(record=existing, skipped=True, research_ready=True)
    finally:
        catalog.close()

    raw_dir = layout.raw_dir(dataset_id, version)
    dest = raw_dir / source.name
    if not dest.exists() or sha256_file(dest) != checksum:
        shutil.copy2(source, dest)
    bars, convention = parse_ohlcv_csv(
        dest,
        data_kind=data_kind,
        dataset_version=version,
        source_id=source.name,
        calendar=calendar,
    )
    raw_bytes = dest.read_bytes()
    note = (
        "WARN: available_time uses session close 15:30 IST because the source had no timestamp"
        if convention == "session_close"
        else "explicit timestamps"
    )
    result = ingest_bars(
        layout,
        bars,
        dataset_id=dataset_id,
        version=version,
        source=str(source),
        data_kind=data_kind,
        raw_name=source.name,
        raw_bytes=raw_bytes,
        calendar_version=calendar.version,
        availability_convention=convention,
    )
    if convention == "session_close":
        catalog = DatasetCatalog(layout)
        try:
            record = result.record.model_copy(
                update={"notes": (result.record.notes + " " + note).strip()}
            )
            catalog.upsert(record)
            result = result.model_copy(update={"record": record})
        finally:
            catalog.close()
    return result


def materialize_synthetic(
    layout: FabricLayout,
    *,
    n_days: int = 80,
    dataset_id: str = SYNTHETIC_DATASET_ID,
    version: str = SYNTHETIC_VERSION,
) -> IngestResult:
    provider = MemoryBarProvider(n_days=n_days)
    flat: list[OHLCVBar] = []
    for series in provider.all_bars().values():
        flat.extend(series)
    stamped = stamp_bars(
        flat,
        dataset_version=version,
        source_id="memory_synthetic_nse",
        data_kind=DataKind.SYNTHETIC,
    )
    raw_bytes = bars_to_csv_bytes(stamped)
    return ingest_bars(
        layout,
        stamped,
        dataset_id=dataset_id,
        version=version,
        source="memory_synthetic_nse",
        data_kind=DataKind.SYNTHETIC,
        raw_name="synthetic_nse.csv",
        raw_bytes=raw_bytes,
        calendar_version="weekday-v1",
        availability_convention="explicit",
    )
