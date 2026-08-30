"""Quantile buckets of a feature vs forward labels. Spread is not trade authorization."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.alpha.ic import align_panels
from quantlab.features.engine import Panel
from quantlab.math.metrics import cross_sectional_ranks, realized_vol


class QuantileBucket(BaseModel):
    quantile: int
    mean_forward: float | None = None
    median_forward: float | None = None
    vol_forward: float | None = None
    hit_rate: float | None = None
    n: int = 0


class QuantileReport(BaseModel):
    schema_version: str = "1"
    buckets: list[QuantileBucket] = Field(default_factory=list)
    long_short_spread: float | None = None
    monotonicity: float | None = None
    n_buckets: int = 5
    note: str = "long-short spread is a research diagnostic, not trade authorization"


def assign_quantiles(scores: dict[str, float], n_buckets: int = 5) -> dict[str, int]:
    ranks = cross_sectional_ranks(scores)
    assigned: dict[str, int] = {}
    for key, rank in ranks.items():
        bucket = int(rank * n_buckets) + 1
        if bucket > n_buckets:
            bucket = n_buckets
        assigned[key] = bucket
    return assigned


def quantile_analysis(
    feature: Panel,
    label: Panel,
    n_buckets: int = 5,
    expected_direction: str = "long_high",
) -> QuantileReport:
    grouped: dict[int, list[float]] = {i: [] for i in range(1, n_buckets + 1)}
    for scores, fwd in align_panels(feature, label):
        buckets = assign_quantiles(scores, n_buckets)
        for key, q in buckets.items():
            grouped[q].append(fwd[key])
    buckets_out: list[QuantileBucket] = []
    means: dict[int, float] = {}
    for q in range(1, n_buckets + 1):
        xs = grouped[q]
        mean = None if not xs else sum(xs) / len(xs)
        if mean is not None:
            means[q] = mean
        buckets_out.append(
            QuantileBucket(
                quantile=q,
                mean_forward=mean,
                median_forward=None if not xs else sorted(xs)[len(xs) // 2],
                vol_forward=realized_vol(xs),
                hit_rate=None if not xs else sum(1 for v in xs if v > 0) / len(xs),
                n=len(xs),
            )
        )
    spread = None
    if 1 in means and n_buckets in means:
        spread = means[n_buckets] - means[1]
        if expected_direction == "long_low":
            spread = -spread
    mono_pairs = 0
    comparable = 0
    for q in range(1, n_buckets):
        if q in means and (q + 1) in means:
            comparable += 1
            left, right = means[q], means[q + 1]
            if expected_direction == "long_low":
                if right <= left:
                    mono_pairs += 1
            elif right >= left:
                mono_pairs += 1
    monotonicity = None if comparable == 0 else mono_pairs / comparable
    return QuantileReport(
        buckets=buckets_out,
        long_short_spread=spread,
        monotonicity=monotonicity,
        n_buckets=n_buckets,
    )
