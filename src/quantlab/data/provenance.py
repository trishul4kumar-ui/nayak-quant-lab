"""Immutable dataset provenance. Changing bytes creates a new version."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from quantlab.data.fabric.checksums import sha256_bytes, sha256_file
from quantlab.data.fabric.types import DataKind


class DatasetProvenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    dataset_id: str
    version: str
    source: str
    source_uri_or_reference: str = ""
    retrieved_at: datetime | None = None
    published_at: datetime | None = None
    coverage_start: datetime | None = None
    coverage_end: datetime | None = None
    schema_version: str = "ohlcv-v1"
    checksum_sha256: str
    row_count: int = 0
    security_count: int = 0
    data_kind: DataKind = DataKind.SYNTHETIC
    license: str = "unspecified"
    created_at: datetime = Field(default_factory=lambda: datetime(2024, 1, 15, tzinfo=UTC))
    note: str = "Missing provenance is NOT_TESTED, never silently repaired."


def provenance_from_bytes(
    payload: bytes,
    *,
    dataset_id: str,
    version: str,
    source: str,
    data_kind: DataKind = DataKind.SYNTHETIC,
    row_count: int = 0,
    security_count: int = 0,
) -> DatasetProvenance:
    return DatasetProvenance(
        dataset_id=dataset_id,
        version=version,
        source=source,
        checksum_sha256=sha256_bytes(payload),
        data_kind=data_kind,
        row_count=row_count,
        security_count=security_count,
    )


def verify_bytes(payload: bytes, expected: str) -> bool:
    return sha256_bytes(payload) == expected


def verify_file(path: object, expected: str) -> bool:
    from pathlib import Path

    return sha256_file(Path(str(path))) == expected
