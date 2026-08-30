"""Information coefficient vs forward labels. IC is a diagnostic, not a promotion score."""

from __future__ import annotations

import math

from pydantic import BaseModel, Field

from quantlab.domain.research import CheckResult
from quantlab.features.engine import Panel
from quantlab.research.cross_section import pearson_ic, spearman_ic


class FeatureICReport(BaseModel):
    schema_version: str = "1"
    pearson_mean: float | None = None
    spearman_mean: float | None = None
    median: float | None = None
    std: float | None = None
    ir: float | None = None
    hit_rate: float | None = None
    t_stat: float | None = None
    n: int = 0
    min_sample: int = 8
    status: CheckResult = CheckResult.NOT_TESTED
    points: list[float] = Field(default_factory=list)
    note: str = "daily IC is not treated as IID; t-stat is descriptive"


def align_panels(feature: Panel, label: Panel) -> list[tuple[dict[str, float], dict[str, float]]]:
    aligned: list[tuple[dict[str, float], dict[str, float]]] = []
    for as_of, scores in feature.items():
        fwd = label.get(as_of)
        if fwd is None:
            continue
        keys = [k for k in scores if k in fwd]
        if len(keys) < 3:
            continue
        aligned.append(({k: scores[k] for k in keys}, {k: fwd[k] for k in keys}))
    return aligned


def information_coefficient(
    feature: Panel,
    label: Panel,
    min_sample: int = 8,
) -> FeatureICReport:
    aligned = align_panels(feature, label)
    spearman: list[float] = []
    pearson: list[float] = []
    for scores, fwd in aligned:
        s = spearman_ic(scores, fwd)
        p = pearson_ic(scores, fwd)
        if s is not None:
            spearman.append(s)
        if p is not None:
            pearson.append(p)
    n = len(spearman)
    if n == 0:
        return FeatureICReport(n=0, min_sample=min_sample, status=CheckResult.NOT_TESTED)
    mean = sum(spearman) / n
    median = sorted(spearman)[n // 2]
    var = sum((v - mean) ** 2 for v in spearman) / n
    std = math.sqrt(var)
    ir = None if std == 0.0 else mean / std
    hit = sum(1 for v in spearman if v > 0) / n
    t_stat = None
    status = CheckResult.NOT_TESTED
    if n >= min_sample and std > 0:
        t_stat = mean / (std / math.sqrt(n))
        status = CheckResult.PASS
    elif n >= min_sample:
        status = CheckResult.PASS
    return FeatureICReport(
        pearson_mean=None if not pearson else sum(pearson) / len(pearson),
        spearman_mean=mean,
        median=median,
        std=std,
        ir=ir,
        hit_rate=hit,
        t_stat=t_stat,
        n=n,
        min_sample=min_sample,
        status=status,
        points=list(spearman),
        note=(
            "daily IC is not treated as IID; t-stat is descriptive"
            if n >= min_sample
            else f"n={n} < min_sample={min_sample}; t-stat NOT_TESTED"
        ),
    )
