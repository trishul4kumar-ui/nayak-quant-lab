"""Cross-sectional IC. Holding-period / decay consumers import from here."""

from __future__ import annotations

import math

from pydantic import BaseModel, Field


def spearman_ic(scores: dict[str, float], forward: dict[str, float]) -> float | None:
    keys = [k for k in scores if k in forward]
    if len(keys) < 3:
        return None
    sx = _ranks([scores[k] for k in keys])
    sy = _ranks([forward[k] for k in keys])
    return _pearson(sx, sy)


def pearson_ic(x: dict[str, float], y: dict[str, float]) -> float | None:
    keys = [k for k in x if k in y]
    if len(keys) < 3:
        return None
    xs = [float(x[k]) for k in keys]
    ys = [float(y[k]) for k in keys]
    return _pearson(xs, ys)


def _ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(x: list[float], y: list[float]) -> float | None:
    n = len(x)
    if n < 3:
        return None
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    dx = sum((v - mx) ** 2 for v in x)
    dy = sum((v - my) ** 2 for v in y)
    if dx <= 0 or dy <= 0:
        return None
    return num / (math.sqrt(dx) * math.sqrt(dy))


class CrossSectionReport(BaseModel):
    schema_version: str = "1"
    mean_ic: float | None = None
    ic_std: float | None = None
    ic_ir: float | None = None
    n: int = 0
    points: list[float] = Field(default_factory=list)
    note: str = "rank IC is a research diagnostic, not a promotion score"


def summarize_ic(values: list[float]) -> CrossSectionReport:
    if len(values) < 2:
        return CrossSectionReport(n=len(values), points=list(values))
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    std = var**0.5
    ir = None if std == 0.0 else mean / std
    return CrossSectionReport(
        mean_ic=mean, ic_std=std, ic_ir=ir, n=len(values), points=list(values)
    )
