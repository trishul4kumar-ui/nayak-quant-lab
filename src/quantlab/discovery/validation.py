"""Walk-forward / holdout scoring. Holdout is not used for selection."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from quantlab.alpha.ic import information_coefficient
from quantlab.discovery.evaluator import slice_panel
from quantlab.features.engine import Panel


class SplitSpec(BaseModel):
    train: list[datetime]
    validation: list[datetime]
    holdout: list[datetime]


class ValidationScores(BaseModel):
    train_ic: float | None = None
    validation_ic: float | None = None
    holdout_ic: float | None = None
    walk_forward_windows: int = 0
    walk_forward_ic: float | None = None
    holdout_used_for_selection: bool = False


def split_dates(dates: list[datetime]) -> SplitSpec:
    ordered = list(dates)
    n = len(ordered)
    a = max(int(n * 0.60), 8)
    b = max(int(n * 0.80), a + 4)
    return SplitSpec(train=ordered[:a], validation=ordered[a:b], holdout=ordered[b:])


def score_splits(panel: Panel, label: Panel, splits: SplitSpec) -> ValidationScores:
    def _ic(fold: list[datetime]) -> float | None:
        report = information_coefficient(
            slice_panel(panel, fold), slice_panel(label, fold), min_sample=5
        )
        return report.spearman_mean

    windows = 0
    wf: list[float] = []
    train = splits.train
    step = max(len(train) // 3, 8)
    for end in range(step, len(train) + 1, step):
        fold = train[:end]
        value = _ic(fold)
        if value is not None:
            wf.append(value)
            windows += 1
    return ValidationScores(
        train_ic=_ic(splits.train),
        validation_ic=_ic(splits.validation),
        holdout_ic=_ic(splits.holdout),
        walk_forward_windows=windows,
        walk_forward_ic=None if not wf else sum(wf) / len(wf),
        holdout_used_for_selection=False,
    )
