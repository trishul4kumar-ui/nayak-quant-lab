"""Training-only scaling. Validation/test statistics never enter the transformer."""

from __future__ import annotations

import math

from pydantic import BaseModel, Field

from quantlab.core.errors import ModelError
from quantlab.learning.definition import ScalingMethod


class FittedScaler(BaseModel):
    method: ScalingMethod
    mean: list[float] = Field(default_factory=list)
    std: list[float] = Field(default_factory=list)
    median: list[float] = Field(default_factory=list)
    iqr: list[float] = Field(default_factory=list)


def fit_scaler(rows: list[list[float]], method: ScalingMethod) -> FittedScaler:
    if not rows:
        raise ModelError("insufficient_history: empty matrix for scaler")
    p = len(rows[0])
    cols = [[row[j] for row in rows] for j in range(p)]
    if method is ScalingMethod.NONE:
        return FittedScaler(method=method)
    if method is ScalingMethod.ZSCORE:
        mean = [_mean(col) for col in cols]
        std = [_std(col) for col in cols]
        if any(s <= 0 or not math.isfinite(s) for s in std):
            raise ModelError("constant_feature")
        return FittedScaler(method=method, mean=mean, std=std)
    median = [_quantile(col, 0.5) for col in cols]
    q1 = [_quantile(col, 0.25) for col in cols]
    q3 = [_quantile(col, 0.75) for col in cols]
    iqr = [q3[j] - q1[j] for j in range(p)]
    if any(v <= 0 or not math.isfinite(v) for v in iqr):
        raise ModelError("constant_feature")
    return FittedScaler(method=method, median=median, iqr=iqr)


def apply_scaler(rows: list[list[float]], scaler: FittedScaler) -> list[list[float]]:
    if scaler.method is ScalingMethod.NONE:
        return [list(row) for row in rows]
    out: list[list[float]] = []
    for row in rows:
        scaled: list[float] = []
        for j, value in enumerate(row):
            if scaler.method is ScalingMethod.ZSCORE:
                scaled.append((value - scaler.mean[j]) / scaler.std[j])
            else:
                scaled.append((value - scaler.median[j]) / scaler.iqr[j])
        out.append(scaled)
    return out


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    mu = _mean(values)
    var = sum((v - mu) ** 2 for v in values) / len(values)
    return math.sqrt(var)


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    idx = q * (len(ordered) - 1)
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    if lo == hi:
        return ordered[lo]
    w = idx - lo
    return ordered[lo] * (1.0 - w) + ordered[hi] * w
