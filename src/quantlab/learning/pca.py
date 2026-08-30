"""Training-only PCA. Full-sample components are leakage when used predictively."""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, Field

from quantlab.core.errors import ModelError


class FittedPCA(BaseModel):
    mean: list[float] = Field(default_factory=list)
    components: list[list[float]] = Field(default_factory=list)
    explained_variance: list[float] = Field(default_factory=list)
    explained_variance_ratio: list[float] = Field(default_factory=list)
    n_components: int = 0


def fit_pca(x_rows: list[list[float]], n_components: int) -> FittedPCA:
    x = np.asarray(x_rows, dtype=np.float64)
    if x.size == 0:
        raise ModelError("insufficient_history")
    if not np.isfinite(x).all():
        raise ModelError("non_finite_values")
    k = min(n_components, x.shape[0], x.shape[1])
    if k < 1:
        raise ModelError("insufficient_history")
    mean = x.mean(axis=0)
    xc = x - mean
    _, s, vt = np.linalg.svd(xc, full_matrices=False)
    var = (s**2) / max(x.shape[0] - 1, 1)
    total = float(var.sum()) if float(var.sum()) > 0 else 1.0
    comps = vt[:k]
    ev = [float(v) for v in var[:k]]
    return FittedPCA(
        mean=[float(v) for v in mean.tolist()],
        components=[[float(v) for v in row] for row in comps.tolist()],
        explained_variance=ev,
        explained_variance_ratio=[v / total for v in ev],
        n_components=k,
    )


def apply_pca(x_rows: list[list[float]], pca: FittedPCA) -> list[list[float]]:
    x = np.asarray(x_rows, dtype=np.float64)
    mean = np.asarray(pca.mean, dtype=np.float64)
    comps = np.asarray(pca.components, dtype=np.float64)
    projected = (x - mean) @ comps.T
    return [[float(v) for v in row] for row in projected.tolist()]
