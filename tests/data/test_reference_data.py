from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from quantlab.core.errors import DataIntegrityError
from quantlab.data.fabric.fundamentals import ReferenceDataStore, ReferenceKind
from quantlab.data.fabric.types import DataKind


def document() -> dict[str, object]:
    return {
        "dataset_id": "reference-demo",
        "version": "v1",
        "source": "synthetic_fixture",
        "source_version": "1",
        "data_kind": "synthetic",
        "observations": [
            fact("sector", "sector", "technology", "2024-01-01", "2024-01-05"),
            fact("sector", "sector", "finance", "2024-06-01", "2024-05-01"),
            fact("market_cap", "market_cap", 150.0, "2024-04-01", "2024-04-02"),
            fact(
                "fundamental", "revenue", 10.0, "2023-12-31", "2024-02-01", period_end="2023-12-31"
            ),
            fact(
                "fundamental", "revenue", 20.0, "2024-03-31", "2024-04-25", period_end="2024-03-31"
            ),
            fact(
                "fundamental",
                "revenue",
                11.0,
                "2023-12-31",
                "2024-05-01",
                period_end="2023-12-31",
                revision=2,
            ),
        ],
    }


def fact(
    kind: str,
    metric: str,
    value: object,
    effective: str,
    available: str,
    *,
    period_end: str | None = None,
    revision: int = 1,
) -> dict[str, object]:
    return {
        "security_id": "NSE:TCS",
        "kind": kind,
        "metric": metric,
        "value": value,
        "unit": "INR" if kind != "sector" else "classification",
        "revision": revision,
        "effective_time": f"{effective}T00:00:00Z",
        "publication_time": f"{available}T00:00:00Z",
        "available_time": f"{available}T00:00:00Z",
        "period_end": period_end,
    }


def raw(doc: dict[str, object]) -> bytes:
    return json.dumps(doc).encode()


def at(day: str) -> datetime:
    return datetime.fromisoformat(f"{day}T12:00:00+00:00")


def test_pit_revisions_effective_time_and_availability(tmp_path: Path) -> None:
    store = ReferenceDataStore(tmp_path / "reference.sqlite")
    store.ingest_json(raw(document()))

    def query(kind: ReferenceKind, metric: str, date: str):  # type: ignore[no-untyped-def]
        return store.as_of(
            "reference-demo",
            "v1",
            security_id="NSE:TCS",
            kind=kind,
            metric=metric,
            as_of=at(date),
            allow_synthetic=True,
        )

    assert query(ReferenceKind.SECTOR, "sector", "2024-01-04") is None
    assert query(ReferenceKind.SECTOR, "sector", "2024-05-15").observation.value == "technology"
    assert query(ReferenceKind.SECTOR, "sector", "2024-06-01").observation.value == "finance"
    assert query(ReferenceKind.MARKET_CAP, "market_cap", "2024-04-01") is None
    assert query(ReferenceKind.MARKET_CAP, "market_cap", "2024-04-02").observation.value == 150
    # A later revision of an older accounting period must not replace the newer period.
    assert query(ReferenceKind.FUNDAMENTAL, "revenue", "2024-05-02").observation.value == 20
    assert query(ReferenceKind.FUNDAMENTAL, "missing", "2024-05-02") is None
    store.close()


def test_restart_preserves_source_and_version_and_fails_on_conflict(tmp_path: Path) -> None:
    path = tmp_path / "reference.sqlite"
    first = ReferenceDataStore(path)
    payload = raw(document())
    first.ingest_json(payload)
    first.ingest_json(payload)
    first.close()
    second = ReferenceDataStore(path)
    result = second.as_of(
        "reference-demo",
        "v1",
        security_id="NSE:TCS",
        kind=ReferenceKind.SECTOR,
        metric="sector",
        as_of=at("2024-05-01"),
        allow_synthetic=True,
    )
    assert result is not None
    assert result.data_kind is DataKind.SYNTHETIC
    assert len(result.source_checksum) == 64
    assert result.source_version == "1"
    changed = document()
    changed["source_version"] = "2"
    with pytest.raises(DataIntegrityError, match="version conflict"):
        second.ingest_json(raw(changed))
    with pytest.raises(DataIntegrityError, match="unavailable"):
        second.get_dataset("missing", "v1")
    second.close()


def test_no_synthetic_implicit_or_production_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "reference.sqlite"
    store = ReferenceDataStore(path)
    store.ingest_json(raw(document()))
    with pytest.raises(DataIntegrityError, match="synthetic"):
        store.as_of(
            "reference-demo",
            "v1",
            security_id="NSE:TCS",
            kind=ReferenceKind.SECTOR,
            metric="sector",
            as_of=at("2024-05-01"),
        )
    monkeypatch.delenv("_QUANTLAB_TEST_FIXTURES")
    with pytest.raises(DataIntegrityError, match="REAL_DATA_REQUIRED"):
        store.as_of(
            "reference-demo",
            "v1",
            security_id="NSE:TCS",
            kind=ReferenceKind.SECTOR,
            metric="sector",
            as_of=at("2024-05-01"),
            allow_synthetic=True,
        )
    store.close()


def test_utc_cutoff_required_and_tampered_source_rejected(tmp_path: Path) -> None:
    path = tmp_path / "reference.sqlite"
    store = ReferenceDataStore(path)
    store.ingest_json(raw(document()))
    with pytest.raises(ValueError, match="timezone-aware"):
        store.as_of(
            "reference-demo",
            "v1",
            security_id="NSE:TCS",
            kind=ReferenceKind.SECTOR,
            metric="sector",
            as_of=datetime(2024, 1, 1),
        )
    store.close()


def test_resealed_raw_document_is_rejected_against_audit(tmp_path: Path) -> None:
    path = tmp_path / "reference.sqlite"
    store = ReferenceDataStore(path)
    store.ingest_json(raw(document()))
    store.close()
    changed = document()
    changed["source_version"] = "tampered"
    changed_raw = raw(changed)
    forged = {
        "raw_base64": base64.b64encode(changed_raw).decode("ascii"),
        "source_checksum": hashlib.sha256(changed_raw).hexdigest(),
    }
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE control_plane_records SET payload_json = ?", (json.dumps(forged),)
        )
    store = ReferenceDataStore(path)
    with pytest.raises(DataIntegrityError, match="integrity"):
        store.get_dataset("reference-demo", "v1")
    store.close()
    with sqlite3.connect(path) as connection:
        payload = connection.execute("SELECT payload_json FROM control_plane_records").fetchone()[0]
        content = json.loads(payload)
        content["source_checksum"] = "0" * 64
        connection.execute(
            "UPDATE control_plane_records SET payload_json = ?", (json.dumps(content),)
        )
    store = ReferenceDataStore(path)
    with pytest.raises(DataIntegrityError, match="integrity"):
        store.get_dataset("reference-demo", "v1")
    store.close()


@pytest.mark.parametrize(
    "mutation", ["early_available", "naive", "nan", "duplicate", "real_fixture"]
)
def test_invalid_source_documents_rejected(tmp_path: Path, mutation: str) -> None:
    doc = document()
    rows = doc["observations"]
    assert isinstance(rows, list)
    if mutation == "early_available":
        rows[0]["publication_time"] = "2024-01-06T00:00:00Z"
    elif mutation == "naive":
        rows[0]["effective_time"] = "2024-01-01T00:00:00"
    elif mutation == "nan":
        rows[2]["value"] = float("nan")
    elif mutation == "duplicate":
        rows.append(rows[0].copy())
    else:
        doc["data_kind"] = "real"
    store = ReferenceDataStore(tmp_path / "reference.sqlite")
    with pytest.raises(DataIntegrityError):
        store.ingest_json(raw(doc))
    store.close()


def test_timezones_are_compared_as_instants(tmp_path: Path) -> None:
    doc = document()
    store = ReferenceDataStore(tmp_path / "reference.sqlite")
    store.ingest_json(raw(doc))
    cutoff = datetime.fromisoformat("2024-01-05T05:30:00+05:30")
    result = store.as_of(
        "reference-demo",
        "v1",
        security_id="NSE:TCS",
        kind=ReferenceKind.SECTOR,
        metric="sector",
        as_of=cutoff,
        allow_synthetic=True,
    )
    assert result is not None and result.observation.value == "technology"
    assert result.as_of.astimezone(UTC).hour == 0
    store.close()
