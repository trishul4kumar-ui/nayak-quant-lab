"""Gross, net, concentration. Beta/sector/factor stay NOT_TESTED without PIT data."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.core.errors import DataIntegrityError
from quantlab.data.fabric.fundamentals import ReferenceDataStore, ReferenceKind
from quantlab.domain.research import CheckResult


@dataclass(frozen=True)
class SectorReferenceInput:
    store: ReferenceDataStore
    dataset_id: str
    version: str
    as_of: datetime
    security_ids: dict[str, str]
    allow_synthetic: bool = False


class SectorExposureReport(BaseModel):
    status: CheckResult
    dataset_id: str
    version: str
    as_of: datetime
    source: str = ""
    source_checksum: str = ""
    data_kind: str = ""
    gross_by_sector: dict[str, float] = Field(default_factory=dict)
    missing: list[str] = Field(default_factory=list)
    note: str = ""


class ExposureReport(BaseModel):
    schema_version: str = "1"
    n_positions: int = 0
    gross: float = 0.0
    net: float = 0.0
    cash: float = 0.0
    max_weight: float = 0.0
    top5_weight: float = 0.0
    top10_weight: float = 0.0
    hhi: float | None = None
    effective_n: float | None = None
    beta: CheckResult = CheckResult.NOT_TESTED
    sector: CheckResult = CheckResult.NOT_TESTED
    sector_detail: SectorExposureReport | None = None
    factor: CheckResult = CheckResult.NOT_TESTED
    liquidity: CheckResult = CheckResult.NOT_TESTED
    capacity: CheckResult = CheckResult.NOT_TESTED
    benchmark: str = "NOT_AVAILABLE"
    note: str = "beta/sector/cap/ADV/benchmark are NOT_TESTED until PIT series exist"


def sector_exposure(
    weights: dict[str, float], *, reference: SectorReferenceInput
) -> SectorExposureReport:
    """Compute gross sector weights from one explicitly versioned PIT source.

    A calculation is research evidence only: source completeness, licence and
    historical knowledge timestamps are not independently certified here.
    """
    if reference.as_of.utcoffset() is None:
        raise DataIntegrityError("sector exposure cutoff must be timezone-aware")
    if any(not math.isfinite(value) for value in weights.values()):
        raise DataIntegrityError("sector exposure requires finite portfolio weights")
    held = {key: value for key, value in weights.items() if abs(value) > 1e-12}
    missing: list[str] = []
    grouped: dict[str, float] = {}
    source = ""
    checksum = ""
    data_kind = ""
    for name, weight in sorted(held.items()):
        security_id = reference.security_ids.get(name)
        if not security_id:
            missing.append(name)
            continue
        result = reference.store.as_of(
            reference.dataset_id,
            reference.version,
            security_id=security_id,
            kind=ReferenceKind.SECTOR,
            metric="sector",
            as_of=reference.as_of,
            allow_synthetic=reference.allow_synthetic,
        )
        if result is None:
            missing.append(name)
            continue
        if checksum and (checksum != result.source_checksum or source != result.source):
            raise DataIntegrityError("reference dataset changed during exposure calculation")
        source, checksum = result.source, result.source_checksum
        data_kind = result.data_kind.value
        value = result.observation.value
        if not isinstance(value, str) or not value.strip():
            raise DataIntegrityError("invalid sector classification")
        grouped[value] = grouped.get(value, 0.0) + abs(weight)
    if missing or not held:
        return SectorExposureReport(
            status=CheckResult.NOT_TESTED,
            dataset_id=reference.dataset_id,
            version=reference.version,
            as_of=reference.as_of,
            source=source,
            source_checksum=checksum,
            data_kind=data_kind,
            missing=missing,
            note="missing sector coverage or no positions; no aggregate is claimed",
        )
    return SectorExposureReport(
        status=CheckResult.WARN,
        dataset_id=reference.dataset_id,
        version=reference.version,
        as_of=reference.as_of,
        source=source,
        source_checksum=checksum,
        data_kind=data_kind,
        gross_by_sector=grouped,
        note="computed from declared PIT reference data; source validation remains required",
    )


def exposure_report(
    weights: dict[str, float], *, sector_reference: SectorReferenceInput | None = None
) -> ExposureReport:
    sector_detail = (
        sector_exposure(weights, reference=sector_reference)
        if sector_reference is not None else None
    )
    held = {k: v for k, v in weights.items() if abs(v) > 1e-12}
    gross = sum(abs(v) for v in held.values())
    net = sum(held.values())
    abs_w = sorted((abs(v) for v in held.values()), reverse=True)
    if gross <= 0:
        return ExposureReport(n_positions=0, cash=1.0, sector_detail=sector_detail)
    shares = [w / gross for w in abs_w]
    hhi = sum(s * s for s in shares)
    return ExposureReport(
        n_positions=len(held),
        gross=gross,
        net=net,
        cash=1.0 - net,
        max_weight=abs_w[0] if abs_w else 0.0,
        top5_weight=sum(abs_w[:5]),
        top10_weight=sum(abs_w[:10]),
        hhi=hhi,
        effective_n=None if hhi <= 0 else 1.0 / hhi,
        sector=sector_detail.status if sector_detail is not None else CheckResult.NOT_TESTED,
        sector_detail=sector_detail,
        note=(
            "sector exposure is derived from declared PIT data; beta/cap/ADV/benchmark remain "
            "NOT_TESTED"
            if sector_detail is not None and sector_detail.status is CheckResult.WARN
            else "beta/sector/cap/ADV/benchmark are NOT_TESTED until PIT series exist"
        ),
    )
