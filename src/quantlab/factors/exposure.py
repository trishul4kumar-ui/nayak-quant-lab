"""Factor exposure matrix B and portfolio exposures B_p = wᵀB."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.core.errors import AlignmentError
from quantlab.domain.research import CheckResult
from quantlab.features.engine import Panel
from quantlab.research.attribution import AttributionReport, FactorExposure


class ExposureMatrix(BaseModel):
    schema_version: str = "1"
    as_of: datetime
    names: list[str] = Field(default_factory=list)
    factor_ids: list[str] = Field(default_factory=list)
    matrix: list[list[float | None]] = Field(default_factory=list)
    status: CheckResult = CheckResult.PASS
    note: str = "rows are security_id; columns are factor_id; missing is None, not zero"


class PortfolioFactorExposure(BaseModel):
    schema_version: str = "1"
    as_of: datetime | None = None
    exposures: dict[str, float] = Field(default_factory=dict)
    missing: list[str] = Field(default_factory=list)
    status: CheckResult = CheckResult.PASS
    note: str = "B_p = sum_i w_i B_i; unknown B_i is omitted and listed in missing"


def exposure_matrix(
    factor_panels: dict[str, Panel],
    as_of: datetime,
) -> ExposureMatrix:
    names: set[str] = set()
    for panel in factor_panels.values():
        names |= set(panel.get(as_of, {}))
    ordered_names = sorted(names)
    factor_ids = sorted(factor_panels)
    matrix: list[list[float | None]] = []
    for name in ordered_names:
        row: list[float | None] = []
        for fid in factor_ids:
            value = factor_panels[fid].get(as_of, {}).get(name)
            row.append(None if value is None else float(value))
        matrix.append(row)
    return ExposureMatrix(as_of=as_of, names=ordered_names, factor_ids=factor_ids, matrix=matrix)


def portfolio_exposures(
    weights: dict[str, float],
    matrix: ExposureMatrix,
) -> PortfolioFactorExposure:
    if not matrix.names:
        return PortfolioFactorExposure(
            as_of=matrix.as_of,
            status=CheckResult.NOT_TESTED,
            note="empty exposure matrix",
        )
    index = {name: i for i, name in enumerate(matrix.names)}
    exposures: dict[str, float] = {}
    missing: list[str] = []
    for j, fid in enumerate(matrix.factor_ids):
        total = 0.0
        used = 0.0
        for name, weight in weights.items():
            if abs(weight) < 1e-12:
                continue
            row_i = index.get(name)
            if row_i is None:
                missing.append(name)
                continue
            value = matrix.matrix[row_i][j]
            if value is None:
                missing.append(f"{name}:{fid}")
                continue
            total += weight * value
            used += abs(weight)
        if used <= 0:
            missing.append(fid)
            continue
        exposures[fid] = total
    status = CheckResult.WARN if missing else CheckResult.PASS
    return PortfolioFactorExposure(
        as_of=matrix.as_of,
        exposures=exposures,
        missing=sorted(set(missing)),
        status=status,
    )


def active_exposures(
    portfolio: PortfolioFactorExposure,
    benchmark: PortfolioFactorExposure,
) -> PortfolioFactorExposure:
    """Portfolio minus benchmark. Missing on either side is not filled with zero."""
    keys = sorted(set(portfolio.exposures) | set(benchmark.exposures))
    exposures: dict[str, float] = {}
    missing: list[str] = list(portfolio.missing) + list(benchmark.missing)
    for key in keys:
        left = portfolio.exposures.get(key)
        right = benchmark.exposures.get(key)
        if left is None or right is None:
            missing.append(key)
            continue
        exposures[key] = left - right
    status = CheckResult.WARN if missing else CheckResult.PASS
    return PortfolioFactorExposure(
        as_of=portfolio.as_of,
        exposures=exposures,
        missing=sorted(set(missing)),
        status=status,
        note="active = portfolio − benchmark; unknown is not assumed zero",
    )


def as_attribution(report: PortfolioFactorExposure) -> AttributionReport:
    rows = [
        FactorExposure(name=name, value=value, status=CheckResult.PASS)
        for name, value in sorted(report.exposures.items())
    ]
    for name in ("size_log_cap", "value_book_to_market", "quality_roe", "liquidity_adv", "sector"):
        if name not in report.exposures:
            rows.append(
                FactorExposure(
                    name=name,
                    status=CheckResult.NOT_TESTED,
                    note="PIT series not bundled",
                )
            )
    return AttributionReport(
        status=report.status,
        exposures=rows,
        note=report.note,
    )


def require_aligned(left: Panel, right: Panel) -> None:
    if not (set(left) & set(right)):
        raise AlignmentError("factor panels share no decision_time")
