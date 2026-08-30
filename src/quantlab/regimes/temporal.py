"""Temporal diagnostics on PIT state series. Architecture, not a forecasting desk."""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, Field

from quantlab.core.errors import RegimeError
from quantlab.domain.research import CheckResult
from quantlab.regimes.normalize import expanding_zscore, series_of
from quantlab.regimes.snapshot import StateSnapshot


class TemporalReport(BaseModel):
    schema_version: str = "1"
    lag1_autocorr: float | None = None
    mean_velocity: float | None = None
    mean_acceleration: float | None = None
    mean_shift: float | None = None
    adf_status: CheckResult = CheckResult.NOT_TESTED
    mahalanobis: float | None = None
    analog_indices: list[int] = Field(default_factory=list)
    status: CheckResult = CheckResult.PASS
    note: str = "ADF is NOT_TESTED (no bundled unit-root library). Diagnostics are not forecasts."


def velocity(values: list[float | None]) -> list[float | None]:
    out: list[float | None] = [None]
    for i in range(1, len(values)):
        a, b = values[i - 1], values[i]
        out.append(None if a is None or b is None else b - a)
    return out


def acceleration(values: list[float | None]) -> list[float | None]:
    return velocity(velocity(values))


def lag1_autocorr(values: list[float | None], min_obs: int = 8) -> float | None:
    xs = [v for v in values if v is not None]
    if len(xs) < min_obs:
        return None
    x0 = xs[:-1]
    x1 = xs[1:]
    mx0 = sum(x0) / len(x0)
    mx1 = sum(x1) / len(x1)
    num = sum((a - mx0) * (b - mx1) for a, b in zip(x0, x1, strict=True))
    den0 = sum((a - mx0) ** 2 for a in x0) ** 0.5
    den1 = sum((b - mx1) ** 2 for b in x1) ** 0.5
    if den0 <= 0 or den1 <= 0:
        return None
    return float(num / (den0 * den1))


def mean_shift(values: list[float | None]) -> float | None:
    xs = [v for v in values if v is not None]
    if len(xs) < 8:
        return None
    mid = len(xs) // 2
    left, right = xs[:mid], xs[mid:]
    mu0 = sum(left) / len(left)
    mu1 = sum(right) / len(right)
    pooled = (
        (sum((x - mu0) ** 2 for x in left) + sum((x - mu1) ** 2 for x in right)) / len(xs)
    ) ** 0.5
    if pooled <= 0:
        return 0.0
    return float(abs(mu1 - mu0) / pooled)


def mahalanobis_last(vectors: list[dict[str, float]]) -> float | None:
    if len(vectors) < 8:
        return None
    keys = sorted(vectors[0])
    arr = np.asarray([[row[k] for k in keys] for row in vectors], dtype=np.float64)
    mu = arr[:-1].mean(axis=0)
    centered = arr[:-1] - mu
    cov = (centered.T @ centered) / max(len(centered), 1)
    cov = 0.5 * (cov + cov.T)
    try:
        inv = np.linalg.inv(cov)
    except np.linalg.LinAlgError as exc:
        raise RegimeError("singular state covariance; Mahalanobis undefined") from exc
    diff = arr[-1] - mu
    return float(diff @ inv @ diff)


def nearest_analogs(vectors: list[dict[str, float]], k: int = 3) -> list[int]:
    if len(vectors) < k + 1:
        return []
    keys = sorted(vectors[0])
    arr = np.asarray([[row[k_] for k_ in keys] for row in vectors], dtype=np.float64)
    current = arr[-1]
    hist = arr[:-1]
    dist = np.sqrt(((hist - current) ** 2).sum(axis=1))
    order = np.argsort(dist)[:k]
    return [int(i) for i in order.tolist()]


def summarize_temporal(
    snapshots: list[StateSnapshot], field: str = "realized_vol_20"
) -> TemporalReport:
    values = series_of(snapshots, field)
    vel = velocity(values)
    acc = acceleration(values)
    vecs: list[dict[str, float]] = []
    z = expanding_zscore(values)
    for vol, v_z, v_vel in zip(values, z, vel, strict=True):
        if vol is None or v_z is None:
            continue
        vecs.append({"z": v_z, "vol": vol, "vel": 0.0 if v_vel is None else v_vel})
    maha = None
    analogs: list[int] = []
    try:
        maha = mahalanobis_last(vecs) if vecs else None
        analogs = nearest_analogs(vecs) if vecs else []
    except RegimeError:
        maha = None
    finite_vel = [v for v in vel if v is not None]
    finite_acc = [v for v in acc if v is not None]
    return TemporalReport(
        lag1_autocorr=lag1_autocorr(values),
        mean_velocity=None if not finite_vel else sum(finite_vel) / len(finite_vel),
        mean_acceleration=None if not finite_acc else sum(finite_acc) / len(finite_acc),
        mean_shift=mean_shift(values),
        mahalanobis=maha,
        analog_indices=analogs,
    )
