from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from quantlab.core.errors import DataIntegrityError
from quantlab.data.fabric.fundamentals import ReferenceDataStore
from quantlab.domain.research import CheckResult
from quantlab.portfolio.exposures import SectorReferenceInput, exposure_report


def _input(path: Path, *, cutoff: datetime, mapping: dict[str, str]) -> SectorReferenceInput:
    store = ReferenceDataStore(path)
    dataset = {
        "dataset_id": "sectors", "version": "v1", "source": "synthetic_fixture",
        "source_version": "1", "data_kind": "synthetic", "observations": [
            {
                "security_id": "S:AAA", "kind": "sector", "metric": "sector",
                "value": "TECH", "unit": "classification", "revision": 1,
                "effective_time": "2024-01-01T00:00:00Z",
                "publication_time": "2024-01-02T00:00:00Z",
                "available_time": "2024-01-03T00:00:00Z",
            },
            {
                "security_id": "S:BBB", "kind": "sector", "metric": "sector",
                "value": "FINANCE", "unit": "classification", "revision": 1,
                "effective_time": "2024-01-01T00:00:00Z",
                "publication_time": "2024-01-04T00:00:00Z",
                "available_time": "2024-01-05T00:00:00Z",
            },
        ],
    }
    store.ingest_json(json.dumps(dataset).encode())
    return SectorReferenceInput(
        store=store, dataset_id="sectors", version="v1", as_of=cutoff,
        security_ids=mapping, allow_synthetic=True,
    )


def test_portfolio_uses_versioned_known_sector_classification(tmp_path: Path) -> None:
    ref = _input(
        tmp_path / "reference.sqlite", cutoff=datetime(2024, 1, 6, tzinfo=UTC),
        mapping={"NSE:AAA": "S:AAA", "NSE:BBB": "S:BBB"},
    )
    result = exposure_report({"NSE:AAA": 0.4, "NSE:BBB": -0.2}, sector_reference=ref)
    assert result.sector is CheckResult.WARN
    assert result.sector_detail is not None
    assert result.sector_detail.gross_by_sector == {"TECH": 0.4, "FINANCE": 0.2}
    assert result.sector_detail.data_kind == "synthetic"
    assert len(result.sector_detail.source_checksum) == 64
    ref.store.close()


def test_missing_or_future_sector_never_becomes_zero_or_full_coverage(tmp_path: Path) -> None:
    ref = _input(
        tmp_path / "reference.sqlite", cutoff=datetime(2024, 1, 4, tzinfo=UTC),
        mapping={"NSE:AAA": "S:AAA", "NSE:BBB": "S:BBB"},
    )
    result = exposure_report({"NSE:AAA": 0.4, "NSE:BBB": 0.2}, sector_reference=ref)
    assert result.sector is CheckResult.NOT_TESTED
    assert result.sector_detail is not None
    assert result.sector_detail.missing == ["NSE:BBB"]
    assert result.sector_detail.gross_by_sector == {}
    ref.store.close()


def test_invalid_weights_fail_before_sector_calculation(tmp_path: Path) -> None:
    ref = _input(tmp_path / "reference.sqlite", cutoff=datetime(2024, 1, 6, tzinfo=UTC), mapping={})
    with pytest.raises(DataIntegrityError, match="finite"):
        exposure_report({"NSE:AAA": float("nan")}, sector_reference=ref)
    ref.store.close()
