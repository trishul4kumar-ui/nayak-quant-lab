"""Feature-feature correlation. High correlation is redundancy, not more alpha."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.features.engine import Panel
from quantlab.features.quality import aligned_pairs
from quantlab.research.cross_section import _pearson, _ranks, spearman_ic


class PairCorrelation(BaseModel):
    feature_a: str
    feature_b: str
    pearson: float | None
    spearman: float | None
    n: int
    redundant: bool = False
    note: str = ""


class CorrelationReport(BaseModel):
    schema_version: str = "1"
    pairs: list[PairCorrelation] = Field(default_factory=list)
    note: str = "abs(spearman) >= 0.9 is treated as redundant, not confirmatory"


def correlate_panels(
    feature_a: str,
    panel_a: Panel,
    feature_b: str,
    panel_b: Panel,
    redundant_threshold: float = 0.9,
) -> PairCorrelation:
    xs, ys = aligned_pairs(panel_a, panel_b)
    pearson = _pearson(xs, ys) if len(xs) >= 3 else None
    spearman = _pearson(_ranks(xs), _ranks(ys)) if len(xs) >= 3 else None
    score = abs(spearman) if spearman is not None else 0.0
    return PairCorrelation(
        feature_a=feature_a,
        feature_b=feature_b,
        pearson=pearson,
        spearman=spearman,
        n=len(xs),
        redundant=score >= redundant_threshold,
        note="redundant" if score >= redundant_threshold else "",
    )


def mean_daily_spearman(panel_a: Panel, panel_b: Panel) -> float | None:
    values: list[float] = []
    for as_of, row in panel_a.items():
        other = panel_b.get(as_of)
        if other is None:
            continue
        ic = spearman_ic(row, other)
        if ic is not None:
            values.append(ic)
    if not values:
        return None
    return sum(values) / len(values)
