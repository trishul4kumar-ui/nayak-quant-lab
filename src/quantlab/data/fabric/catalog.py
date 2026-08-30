"""Dataset registry. A file on disk is not research-ready."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from quantlab.data.fabric.layout import FabricLayout
from quantlab.data.fabric.types import DataKind, DatasetState


class DatasetRecord(BaseModel):
    dataset_id: str
    version: str
    state: DatasetState
    data_kind: DataKind
    source: str
    checksum: str
    schema_name: str
    coverage: str = ""
    price_adjustment_method: str = "raw_price"
    corporate_action_policy: str = "none"
    calendar_version: str = ""
    universe_version: str = ""
    snapshot_id: str = ""
    notes: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(tz=UTC).isoformat())
    extra: dict[str, str] = Field(default_factory=dict)


class DatasetCatalog:
    def __init__(self, layout: FabricLayout) -> None:
        self.layout = layout
        layout.ensure()
        self._path = layout.catalog_path()
        self._conn = sqlite3.connect(str(self._path))
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS datasets (
                dataset_id TEXT NOT NULL,
                version TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (dataset_id, version)
            )
            """
        )
        self._conn.commit()

    def upsert(self, record: DatasetRecord) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO datasets (dataset_id, version, payload)
            VALUES (?, ?, ?)
            """,
            (record.dataset_id, record.version, record.model_dump_json()),
        )
        self._conn.commit()

    def get(self, dataset_id: str, version: str) -> DatasetRecord | None:
        row = self._conn.execute(
            "SELECT payload FROM datasets WHERE dataset_id = ? AND version = ?",
            (dataset_id, version),
        ).fetchone()
        if row is None:
            return None
        return DatasetRecord.model_validate_json(row[0])

    def find_by_checksum(self, checksum: str) -> DatasetRecord | None:
        rows = self._conn.execute("SELECT payload FROM datasets").fetchall()
        for (payload,) in rows:
            record = DatasetRecord.model_validate_json(payload)
            if record.checksum == checksum:
                return record
        return None

    def list_records(self) -> list[DatasetRecord]:
        rows = self._conn.execute(
            "SELECT payload FROM datasets ORDER BY dataset_id, version"
        ).fetchall()
        return [DatasetRecord.model_validate_json(row[0]) for row in rows]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> DatasetCatalog:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
