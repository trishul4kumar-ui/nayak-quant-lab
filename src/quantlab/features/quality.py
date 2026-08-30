"""Feature quality diagnostics. Coverage is not predictive power."""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, Field

from quantlab.features.engine import Panel
from quantlab.math.metrics import zscore


class PeriodStats(BaseModel):
    period: str
    n: int
    mean: float | None
    std: float | None
    missingness: float
    q50: float | None


class FeatureQualityReport(BaseModel):
    schema_version: str = "1"
    n: int = 0
    coverage: float = 0.0
    missingness: float = 0.0
    unique: int = 0
    mean: float | None = None
    std: float | None = None
    min: float | None = None
    max: float | None = None
    q05: float | None = None
    q25: float | None = None
    q50: float | None = None
    q75: float | None = None
    q95: float | None = None
    outlier_rate: float | None = None
    cs_coverage_mean: float | None = None
    stability: list[PeriodStats] = Field(default_factory=list)
    note: str = "quality describes the feature, not alpha"


def summarize_quality(
    panel: Panel,
    expected_names: int | None = None,
) -> FeatureQualityReport:
    values: list[float] = []
    cs_sizes: list[int] = []
    by_month: dict[str, list[float]] = {}
    n_slots = 0
    n_missing = 0
    for as_of, row in panel.items():
        cs_sizes.append(len(row))
        expected = expected_names if expected_names is not None else len(row)
        n_slots += expected
        n_missing += max(expected - len(row), 0)
        period = f"{as_of.year:04d}-{as_of.month:02d}"
        by_month.setdefault(period, [])
        for value in row.values():
            values.append(value)
            by_month[period].append(value)
    if not values:
        return FeatureQualityReport(n=0, coverage=0.0, missingness=1.0)
    arr = np.asarray(values, dtype=np.float64)
    qs = np.quantile(arr, [0.05, 0.25, 0.5, 0.75, 0.95])
    scaled = zscore(values)
    outliers = sum(1 for z in scaled if abs(z) > 3.0) / len(scaled)
    unique = len({round(v, 12) for v in values})
    coverage = 0.0 if n_slots == 0 else (n_slots - n_missing) / n_slots
    stability = [
        PeriodStats(
            period=period,
            n=len(xs),
            mean=sum(xs) / len(xs),
            std=float(np.std(np.asarray(xs, dtype=np.float64), ddof=0)),
            missingness=0.0,
            q50=float(np.median(np.asarray(xs, dtype=np.float64))),
        )
        for period, xs in sorted(by_month.items())
        if xs
    ]
    return FeatureQualityReport(
        n=len(values),
        coverage=coverage,
        missingness=1.0 - coverage,
        unique=unique,
        mean=float(arr.mean()),
        std=float(arr.std(ddof=0)),
        min=float(arr.min()),
        max=float(arr.max()),
        q05=float(qs[0]),
        q25=float(qs[1]),
        q50=float(qs[2]),
        q75=float(qs[3]),
        q95=float(qs[4]),
        outlier_rate=outliers,
        cs_coverage_mean=sum(cs_sizes) / len(cs_sizes) if cs_sizes else None,
        stability=stability,
    )


def aligned_pairs(
    left: Panel,
    right: Panel,
) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for as_of, row in left.items():
        other = right.get(as_of)
        if other is None:
            continue
        for key, value in row.items():
            if key in other:
                xs.append(value)
                ys.append(other[key])
    return xs, ys
