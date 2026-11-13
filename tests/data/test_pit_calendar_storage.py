from __future__ import annotations

import base64
import json
import sqlite3
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from quantlab.core.errors import DataIntegrityError
from quantlab.data.fabric.calendar import PointInTimeCalendar, _calendar_hash
from quantlab.data.fabric.types import DataKind
from tests.data.test_pit_calendar import DAY, RAW, snapshot


def calendar(path: Path) -> PointInTimeCalendar:
    return PointInTimeCalendar(exchange="NSE", segment="CM", storage_path=path)


def test_restart_preserves_source_version_and_availability(tmp_path: Path) -> None:
    path = tmp_path / "control.sqlite"
    first = calendar(path)
    original = snapshot()
    later = replace(
        original, version="v2", holidays=frozenset(),
        published_at=datetime(2024, 1, 20, tzinfo=UTC),
        available_at=datetime(2024, 1, 21, tzinfo=UTC),
    )
    first.add(original, source_bytes=RAW)
    first.add(later, source_bytes=RAW)
    first.close()
    reopened = calendar(path)
    assert reopened.session_as_of(DAY, datetime(2024, 1, 20, tzinfo=UTC)) is None
    assert reopened.snapshot_as_of(DAY, datetime(2024, 1, 21, tzinfo=UTC)).version == "v2"
    assert reopened.bind("v1", as_of=datetime(2024, 1, 20, tzinfo=UTC)).version == "v1"
    assert reopened.source_bytes("v1") == RAW
    with pytest.raises(DataIntegrityError, match="unavailable"):
        reopened.bind("v2", as_of=datetime(2024, 1, 20, tzinfo=UTC))
    with pytest.raises(DataIntegrityError, match="no sourced calendar"):
        reopened.session_as_of(date(2025, 1, 1), datetime(2024, 2, 1, tzinfo=UTC))
    reopened.close()


def test_version_collisions_do_not_replace_existing_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "control.sqlite"
    left, right = calendar(path), calendar(path)
    original = snapshot()
    left.add(original, source_bytes=RAW)
    with pytest.raises(DataIntegrityError, match="version"):
        right.add(original, source_bytes=RAW)
    with pytest.raises(DataIntegrityError, match="version"):
        right.add(replace(original, holidays=frozenset()), source_bytes=RAW)
    assert right.snapshot_as_of(DAY, datetime(2024, 1, 20, tzinfo=UTC)) == original
    left.close()
    right.close()


def test_missing_newer_snapshot_cannot_silently_restore_older_revision(tmp_path: Path) -> None:
    path = tmp_path / "control.sqlite"
    store = calendar(path)
    store.add(snapshot(), source_bytes=RAW)
    newer = replace(
        snapshot(), version="v2", holidays=frozenset(),
        published_at=datetime(2024, 1, 20, tzinfo=UTC),
        available_at=datetime(2024, 1, 21, tzinfo=UTC),
    )
    store.add(newer, source_bytes=RAW)
    store.close()
    with sqlite3.connect(path) as db:
        db.execute(
            "DELETE FROM control_plane_records WHERE namespace = ? AND identity = ?",
            ("pit_calendar_snapshots", "3:NSE2:CM2:v2"),
        )
    reopened = calendar(path)
    with pytest.raises(DataIntegrityError, match="integrity"):
        reopened.session_as_of(DAY, datetime(2024, 1, 22, tzinfo=UTC))
    reopened.close()


@pytest.mark.parametrize("kind", ["raw", "metadata", "resealed", "audit"])
def test_tampered_payload_or_audit_is_never_used(tmp_path: Path, kind: str) -> None:
    path = tmp_path / "control.sqlite"
    store = calendar(path)
    store.add(snapshot(), source_bytes=RAW)
    store.close()
    with sqlite3.connect(path) as db:
        if kind == "audit":
            db.execute("UPDATE control_plane_audit SET event = 'NOT_REGISTERED'")
        else:
            saved = db.execute("SELECT payload_json FROM control_plane_records").fetchone()
            assert saved is not None
            content = json.loads(saved[0])
            if kind == "raw":
                content["source_base64"] = base64.b64encode(b"modified").decode("ascii")
            elif kind == "metadata":
                content["snapshot"]["holidays"] = []
            else:
                content["snapshot"]["source"] = "another source"
            if kind == "resealed":
                db.execute(
                    "UPDATE control_plane_records SET payload_json = ?, payload_hash = ?",
                    (json.dumps(content), _calendar_hash(content)),
                )
            else:
                db.execute(
                    "UPDATE control_plane_records SET payload_json = ?", (json.dumps(content),)
                )
    reopened = calendar(path)
    with pytest.raises(DataIntegrityError, match="integrity"):
        reopened.session_as_of(DAY, datetime(2024, 1, 20, tzinfo=UTC))
    reopened.close()


def test_synthetic_snapshot_cannot_be_read_outside_test_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "control.sqlite"
    store = calendar(path)
    store.add(snapshot(), source_bytes=RAW)
    store.close()
    monkeypatch.delenv("_QUANTLAB_TEST_FIXTURES")
    reopened = calendar(path)
    with pytest.raises(DataIntegrityError, match="REAL_DATA_REQUIRED"):
        reopened.session_as_of(DAY, datetime(2024, 1, 20, tzinfo=UTC))
    reopened.close()


def test_fixture_cannot_be_relabelled_as_real_in_production(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("_QUANTLAB_TEST_FIXTURES")
    store = calendar(tmp_path / "control.sqlite")
    fake = replace(snapshot(), source="synthetic_fixture", data_kind=DataKind.REAL)
    with pytest.raises(DataIntegrityError, match="REAL_DATA_REQUIRED"):
        store.add(fake, source_bytes=RAW)
    store.close()


def test_explicit_real_label_round_trips_outside_test_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("_QUANTLAB_TEST_FIXTURES")
    path = tmp_path / "control.sqlite"
    store = calendar(path)
    declared = replace(snapshot(), source="declared-source", data_kind=DataKind.REAL)
    store.add(declared, source_bytes=RAW)
    store.close()
    reopened = calendar(path)
    result = reopened.snapshot_as_of(DAY, datetime(2024, 1, 20, tzinfo=UTC))
    assert result.data_kind is DataKind.REAL
    assert reopened.source_bytes("v1") == RAW
    reopened.close()
