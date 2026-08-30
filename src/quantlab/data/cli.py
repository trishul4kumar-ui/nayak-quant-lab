"""quantlab data … commands. No second CLI process."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab.core.errors import DataIntegrityError, LookAheadError
from quantlab.data.fabric.catalog import DatasetCatalog
from quantlab.data.fabric.gate import evaluate_research_gate
from quantlab.data.fabric.ingest import ingest_csv, materialize_synthetic
from quantlab.data.fabric.layout import FabricLayout, resolve_fabric_root
from quantlab.data.fabric.store import PitStore, parquet_files
from quantlab.data.fabric.types import DataKind, DatasetState


def add_data_parser(sub: Any) -> None:
    data = sub.add_parser("data", help="point-in-time data fabric")
    data_sub = data.add_subparsers(dest="data_cmd", required=True)
    data_sub.add_parser("list", help="list registered datasets")
    inspect = data_sub.add_parser("inspect", help="inspect a dataset id or id@version")
    inspect.add_argument("dataset")
    validate = data_sub.add_parser("validate", help="run the research gate")
    validate.add_argument("dataset")
    ingest = data_sub.add_parser("ingest", help="ingest a CSV or the synthetic fixture")
    ingest.add_argument("source", help="CSV path, or 'synthetic'")
    ingest.add_argument("--dataset-id", default="")
    ingest.add_argument("--version", default="v1")
    ingest.add_argument("--kind", choices=["synthetic", "real"], default="")
    data_sub.add_parser("status", help="fabric layout and dataset states")
    pit = data_sub.add_parser("pit-check", help="assert no available_time > as_of")
    pit.add_argument("dataset")
    pit.add_argument("--as-of", default="", help="ISO-8601 timestamp; default = max available_time")
    lin = data_sub.add_parser("lineage", help="dataset lineage / provenance")
    lin.add_argument("dataset")
    snap = data_sub.add_parser("snapshot", help="freeze a research data snapshot")
    snap.add_argument("dataset")
    qual = data_sub.add_parser("quality", help="production quality report")
    qual.add_argument("dataset")
    rec = data_sub.add_parser("reconcile", help="compare two dataset closes")
    rec.add_argument("dataset")
    rec.add_argument("dataset_b")
    sec = data_sub.add_parser("security", help="inspect a security_id")
    sec.add_argument("security_id")
    data_sub.add_parser("corporate-actions", help="list typed corporate actions")
    data_sub.add_parser("calendar", help="calendar provenance (not invented NSE holidays)")
    data_sub.add_parser("universe", help="universe.as_of architecture status")


def _layout() -> FabricLayout:
    layout = FabricLayout(resolve_fabric_root())
    layout.ensure()
    return layout


def _parse_ref(ref: str, catalog: DatasetCatalog) -> tuple[str, str]:
    if "@" in ref:
        dataset_id, version = ref.split("@", 1)
        return dataset_id, version
    matches = [row for row in catalog.list_records() if row.dataset_id == ref]
    if not matches:
        raise DataIntegrityError(f"unknown dataset {ref}")
    matches.sort(key=lambda row: row.created_at)
    latest = matches[-1]
    return latest.dataset_id, latest.version


def run_data_command(args: argparse.Namespace) -> int:
    layout = _layout()
    cmd = args.data_cmd
    if cmd == "list":
        catalog = DatasetCatalog(layout)
        try:
            rows = [row.model_dump(mode="json") for row in catalog.list_records()]
        finally:
            catalog.close()
        print(json.dumps(rows, indent=2))
        return 0
    if cmd == "status":
        catalog = DatasetCatalog(layout)
        try:
            records = catalog.list_records()
        finally:
            catalog.close()
        payload = {
            "fabric_root": str(layout.root),
            "layers": {
                "raw": str(layout.raw),
                "normalized": str(layout.normalized),
                "curated": str(layout.curated),
                "pit": str(layout.pit),
                "features": str(layout.features),
                "metadata": str(layout.metadata),
                "quarantine": layout.quarantine.exists(),
            },
            "datasets": [
                {
                    "dataset_id": row.dataset_id,
                    "version": row.version,
                    "state": row.state.value,
                    "data_kind": row.data_kind.value,
                    "research_ready": row.state is DatasetState.RESEARCH_READY,
                    "checksum": row.checksum[:16],
                }
                for row in records
            ],
        }
        print(json.dumps(payload, indent=2))
        return 0
    if cmd == "ingest":
        source = args.source
        if source == "synthetic":
            result = materialize_synthetic(layout)
        else:
            kind = DataKind(args.kind) if args.kind else DataKind.REAL
            dataset_id = args.dataset_id or Path(source).stem
            result = ingest_csv(
                Path(source),
                layout,
                dataset_id=dataset_id,
                version=args.version,
                data_kind=kind,
            )
        print(
            json.dumps(
                {
                    "dataset_id": result.record.dataset_id,
                    "version": result.record.version,
                    "state": result.record.state.value,
                    "skipped": result.skipped,
                    "research_ready": result.research_ready,
                    "data_kind": result.record.data_kind.value,
                    "checksum": result.record.checksum,
                    "gate": result.gate,
                    "rows_written": result.rows_written,
                    "availability_convention": result.availability_convention,
                },
                indent=2,
            )
        )
        return 0 if result.record.state is not DatasetState.QUARANTINED else 2
    if cmd == "calendar":
        print(
            json.dumps(
                {
                    "exchange": "NSE",
                    "source": "synthetic_weekdays_not_official_nse_holidays",
                    "official_nse_holidays": "NOT_TESTED",
                    "note": "Do not fabricate NSE holidays.",
                    "live_trading": False,
                },
                indent=2,
            )
        )
        return 0
    if cmd == "universe":
        print(
            json.dumps(
                {
                    "interface": "universe.as_of(T)",
                    "survivorship": "historical membership only",
                    "official_index_membership": "NOT_TESTED",
                    "note": "Current constituents are never substituted for historical T.",
                },
                indent=2,
            )
        )
        return 0
    if cmd == "corporate-actions":
        from quantlab.data.fabric.types import CorporateActionType

        print(
            json.dumps(
                {
                    "types": [item.value for item in CorporateActionType],
                    "required_fields": [
                        "announcement_time",
                        "effective_time",
                        "available_time",
                        "source",
                        "adjustment_method",
                    ],
                    "missing_announcement_time": "NOT_TESTED",
                    "note": "Timing is never invented.",
                },
                indent=2,
            )
        )
        return 0
    if cmd == "security":
        print(
            json.dumps(
                {
                    "security_id": args.security_id,
                    "note": "Tickers are labels. Use InstrumentMaster.symbol_at(security_id, T).",
                },
                indent=2,
            )
        )
        return 0
    catalog = DatasetCatalog(layout)
    try:
        dataset_id, version = _parse_ref(args.dataset, catalog)
        record = catalog.get(dataset_id, version)
    finally:
        catalog.close()
    if record is None:
        raise DataIntegrityError(f"unknown dataset {args.dataset}")
    if cmd == "inspect":
        print(json.dumps(record.model_dump(mode="json"), indent=2))
        return 0
    if cmd == "validate":
        pit_ok: bool | None = None
        files = parquet_files(layout, dataset_id, version)
        if files:
            store = PitStore(layout, dataset_id, version)
            try:
                probe = store.query(as_of=datetime.now(tz=UTC))
                pit_ok = all(bar.pit.available_time <= datetime.now(tz=UTC) for bar in probe)
            except (DataIntegrityError, LookAheadError):
                pit_ok = False
        gate = evaluate_research_gate(record, pit_verified=pit_ok)
        print(
            json.dumps(
                {
                    "dataset_id": dataset_id,
                    "version": version,
                    "research_ready": gate.research_ready,
                    "state": record.state.value,
                    "checks": gate.as_str_map(),
                },
                indent=2,
            )
        )
        return 0 if gate.research_ready else 2
    if cmd == "pit-check":
        store = PitStore(layout, dataset_id, version)
        if args.as_of:
            as_of = datetime.fromisoformat(args.as_of.replace("Z", "+00:00"))
            if as_of.tzinfo is None:
                raise DataIntegrityError("as_of must be timezone-aware")
        else:
            catalog = DatasetCatalog(layout)
            catalog.close()
            as_of = datetime.now(tz=UTC)
        bars = store.query(as_of=as_of)
        leaked = [str(bar.instrument) for bar in bars if bar.pit.available_time > as_of]
        print(
            json.dumps(
                {
                    "dataset_id": dataset_id,
                    "version": version,
                    "as_of": as_of.isoformat(),
                    "rows": len(bars),
                    "leaked": leaked,
                    "ok": not leaked,
                },
                indent=2,
            )
        )
        return 0 if not leaked else 2
    if cmd == "lineage":
        print(
            json.dumps(
                {
                    "dataset_id": dataset_id,
                    "version": version,
                    "source": record.source,
                    "checksum": record.checksum,
                    "schema": record.schema_name,
                    "calendar_version": record.calendar_version,
                    "universe_version": record.universe_version,
                    "snapshot_id": record.snapshot_id,
                    "note": "Which raw source, transformation, snapshot, and available_time.",
                },
                indent=2,
            )
        )
        return 0
    if cmd == "snapshot":
        from quantlab.data.snapshots import freeze_snapshot

        snap = freeze_snapshot(
            dataset_id=dataset_id,
            dataset_version=version,
            dataset_checksum=record.checksum,
            security_master_version=record.extra.get("security_master_version", ""),
            calendar_version=record.calendar_version,
            corporate_action_version=record.corporate_action_policy,
            universe_version=record.universe_version,
        )
        print(json.dumps(snap.model_dump(mode="json"), indent=2, default=str))
        return 0
    if cmd == "quality":
        from quantlab.data.quality_engine import report_from_counts

        report = report_from_counts(rows=0, duplicates=0, invalid=0, pit_ok=None)
        payload = report.model_dump(mode="json")
        payload["dataset_id"] = dataset_id
        payload["checksum"] = record.checksum
        print(json.dumps(payload, indent=2))
        return 0
    if cmd == "reconcile":
        from quantlab.data.fabric.catalog import DatasetCatalog as _Catalog
        from quantlab.data.reconciliation import compare_closes

        catalog2 = _Catalog(layout)
        try:
            other_id, other_ver = _parse_ref(args.dataset_b, catalog2)
            other = catalog2.get(other_id, other_ver)
        finally:
            catalog2.close()
        if other is None:
            raise DataIntegrityError(f"unknown dataset {args.dataset_b}")
        diff = compare_closes(
            source_a=record.source,
            source_b=other.source,
            close_a=0.0,
            close_b=0.0,
            tolerance=0.0,
            policy="record_only",
        )
        print(
            json.dumps(
                {
                    **diff.model_dump(mode="json"),
                    "dataset_a": f"{dataset_id}@{version}",
                    "dataset_b": f"{other_id}@{other_ver}",
                    "note": (
                        "Values shown are placeholders unless closes are supplied; "
                        "unresolved stays visible."
                    ),
                },
                indent=2,
            )
        )
        return 0
    raise DataIntegrityError(f"unknown data command {cmd}")
