"""Falsification probes. A failed OOS expression is a successful falsification."""

from __future__ import annotations

import random
from datetime import datetime

from pydantic import BaseModel

from quantlab.alpha.ic import information_coefficient
from quantlab.discovery.evaluator import slice_panel
from quantlab.features.engine import Panel


class FalsificationReport(BaseModel):
    sign_reversal_ic: float | None = None
    label_permutation_ic: float | None = None
    null_constant_ic: float | None = None
    survived: bool = False
    note: str = "falsification is evidence, not promotion"


def falsify_panel(
    panel: Panel,
    label: Panel,
    dates: list[datetime],
    rng: random.Random,
) -> FalsificationReport:
    scores = slice_panel(panel, dates)
    y = slice_panel(label, dates)
    flipped: Panel = {ts: {k: -v for k, v in row.items()} for ts, row in scores.items()}
    permuted = _permute_labels(y, rng)
    constant: Panel = {ts: {k: 1.0 for k in row} for ts, row in scores.items()}
    rev = information_coefficient(flipped, y, min_sample=5)
    perm = information_coefficient(scores, permuted, min_sample=5)
    null = information_coefficient(constant, y, min_sample=5)
    orig = information_coefficient(scores, y, min_sample=5)
    orig_ic = orig.spearman_mean or 0.0
    survived = abs(orig_ic) > abs(perm.spearman_mean or 0.0)
    return FalsificationReport(
        sign_reversal_ic=rev.spearman_mean,
        label_permutation_ic=perm.spearman_mean,
        null_constant_ic=null.spearman_mean,
        survived=survived,
    )


def _permute_labels(label: Panel, rng: random.Random) -> Panel:
    dates = list(label)
    shuffled = dates[:]
    rng.shuffle(shuffled)
    return {src: label[dst] for src, dst in zip(dates, shuffled, strict=True)}
