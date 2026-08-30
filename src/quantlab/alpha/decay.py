"""Predictive IC decay vs forward horizons. Distinct from portfolio holding-period decay."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.alpha.ic import information_coefficient
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.domain.research import CheckResult
from quantlab.features.engine import Panel
from quantlab.labels.definition import forward_return
from quantlab.labels.engine import compute_label_panel


class PredictiveDecayPoint(BaseModel):
    horizon: int
    spearman_mean: float | None
    n: int
    status: CheckResult


class PredictiveDecayReport(BaseModel):
    schema_version: str = "1"
    points: list[PredictiveDecayPoint] = Field(default_factory=list)
    note: str = "feature IC vs P(T+H)/P(T)-1; not portfolio decay"


def predictive_decay(
    feature: Panel,
    bars: dict[InstrumentId, list[OHLCVBar]],
    horizons: tuple[int, ...] = (1, 2, 5, 10, 20, 60),
    min_sample: int = 8,
) -> PredictiveDecayReport:
    points: list[PredictiveDecayPoint] = []
    for horizon in horizons:
        labels = compute_label_panel(forward_return(horizon), bars, list(feature.keys()))
        report = information_coefficient(feature, labels, min_sample=min_sample)
        points.append(
            PredictiveDecayPoint(
                horizon=horizon,
                spearman_mean=report.spearman_mean,
                n=report.n,
                status=report.status,
            )
        )
    return PredictiveDecayReport(points=points)
