"""Multi-objective fitness. Not Sharpe-max. Train fold only."""

from __future__ import annotations

from datetime import datetime
from statistics import NormalDist

from pydantic import BaseModel, Field

from quantlab.alpha.ic import information_coefficient
from quantlab.discovery.complexity import complexity
from quantlab.discovery.definitions import FitnessName
from quantlab.discovery.evaluator import evaluate_expression, slice_panel
from quantlab.discovery.expression import ExprNode
from quantlab.features.engine import Panel


class FitnessVector(BaseModel):
    schema_version: str = "1"
    name: FitnessName = FitnessName.IC_COMPLEXITY_V1
    predictive_score: float = 0.0
    complexity_penalty: float = 0.0
    redundancy_penalty: float = 0.0
    turnover_penalty: float = 0.0
    stability_score: float = 0.0
    coverage_score: float = 0.0
    scalar: float = 0.0
    p_value: float = 1.0
    ic_n: int = 0
    objective_vector: list[float] = Field(default_factory=list)
    pareto_rank: int = 0


def score_expression(
    expr: ExprNode,
    feature_panels: dict[str, Panel],
    label: Panel,
    train_dates: list[datetime],
    *,
    redundancy_penalty: float = 0.0,
    cache: dict[str, Panel] | None = None,
) -> tuple[FitnessVector, Panel]:
    panel = evaluate_expression(expr, feature_panels, cache)
    train_panel = slice_panel(panel, train_dates)
    train_label = slice_panel(label, train_dates)
    ic = information_coefficient(train_panel, train_label, min_sample=5)
    pred = float(ic.spearman_mean or 0.0)
    cx = complexity(expr)
    coverage = 0.0
    if train_dates:
        coverage = sum(1 for ts in train_dates if ts in train_panel) / len(train_dates)
    turnover = _turnover(train_panel)
    p_value = 1.0
    if ic.t_stat is not None:
        p_value = min(1.0, max(2.0 * (1.0 - NormalDist().cdf(abs(ic.t_stat))), 1e-12))
    scalar = pred - 0.04 * cx.score - redundancy_penalty - 0.15 * turnover + 0.05 * coverage
    vector = FitnessVector(
        predictive_score=pred,
        complexity_penalty=cx.score,
        redundancy_penalty=redundancy_penalty,
        turnover_penalty=turnover,
        stability_score=0.0,
        coverage_score=coverage,
        scalar=scalar,
        p_value=p_value,
        ic_n=ic.n,
        objective_vector=[pred, -cx.score, -redundancy_penalty],
    )
    return vector, panel


def _turnover(panel: Panel) -> float:
    dates = sorted(panel)
    if len(dates) < 2:
        return 0.0
    changes = 0.0
    n = 0
    for prev, cur in zip(dates, dates[1:], strict=False):
        a = panel[prev]
        b = panel[cur]
        keys = set(a) & set(b)
        if len(keys) < 2:
            continue
        delta = sum(abs(a[k] - b[k]) for k in keys) / len(keys)
        changes += delta
        n += 1
    return 0.0 if n == 0 else changes / n
