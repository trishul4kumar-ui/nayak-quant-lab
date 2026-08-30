"""PIT ensemble engine. Combine at T using evidence available at T. No second backtester."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from quantlab.adaptive.engine import compute_label_panel_1
from quantlab.core.errors import EnsembleError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.domain.research import CheckResult
from quantlab.ensemble.combine import combine_at, normalize_row, pooled_moments
from quantlab.ensemble.components import predictive_regimes, resolve_component_panels
from quantlab.ensemble.definition import (
    EnsembleDefinition,
    EnsembleLeakFlags,
    EnsemblePrediction,
    EnsembleState,
    Normalization,
    WeightingPolicy,
)
from quantlab.ensemble.diversity import equal_weight_panel
from quantlab.ensemble.stacking import stack_at
from quantlab.ensemble.weighting import compute_weights, weight_turnover
from quantlab.features.engine import Panel, session_calendar
from quantlab.research.cross_section import spearman_ic


class EnsemblePoint(BaseModel):
    as_of: datetime
    ic: float | None = None
    coverage: bool = False
    weights: dict[str, float] = Field(default_factory=dict)
    fallback_equal: bool = False
    regime: str | None = None
    weight_turnover: float | None = None
    pruned: list[str] = Field(default_factory=list)


class EnsembleResult(BaseModel):
    schema_version: str = "1"
    n_predictions: int = 0
    n_scored: int = 0
    mean_ic: float | None = None
    hit_rate: float | None = None
    coverage: float | None = None
    mean_weight_turnover: float | None = None
    quantile_spread: float | None = None
    points: list[EnsemblePoint] = Field(default_factory=list)
    weights_path: list[dict[str, float]] = Field(default_factory=list)
    predictions: Panel = Field(default_factory=dict)
    component_ics: dict[str, float | None] = Field(default_factory=dict)
    equal_weight_ic: float | None = None
    best_component_id: str | None = None
    best_component_ic: float | None = None
    final_state: EnsembleState | None = None
    last_predictions: list[EnsemblePrediction] = Field(default_factory=list)
    n_candidates: int = 1
    search_truncated: bool = False
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = "combine at T using components and weights available at T; label T→T+1 is not used"


def run_ensemble(
    definition: EnsembleDefinition,
    bars: dict[InstrumentId, list[OHLCVBar]],
    *,
    leaks: EnsembleLeakFlags | None = None,
    snapshot_id: str = "",
    predictive: bool = True,
    overrides: dict[str, Panel] | None = None,
    holdout_start: datetime | None = None,
) -> tuple[dict[str, Panel], Panel, EnsembleResult]:
    flags = leaks or EnsembleLeakFlags()
    dates = session_calendar(bars)
    if not dates:
        return {}, {}, EnsembleResult(note="empty calendar")
    labels = compute_label_panel_1(bars, dates)
    panels = resolve_component_panels(definition, bars, dates, overrides=overrides)
    regimes = None
    if definition.regime_model_id:
        regimes = predictive_regimes(
            bars, definition.regime_model_id, predictive=predictive and not flags.future_regime
        )
    stacking = definition.weighting_policy in {
        WeightingPolicy.RIDGE_STACK,
        WeightingPolicy.ELASTIC_STACK,
        WeightingPolicy.OLS_META,
    }
    leaky_norm = _pooled_norm(panels) if flags.future_normalization else None
    predictions: Panel = {}
    points: list[EnsemblePoint] = []
    weights_path: list[dict[str, float]] = []
    previous: dict[str, float] | None = None
    names = definition.component_ids()

    for i, as_of in enumerate(dates):
        hist = _history_dates(dates, i, as_of, holdout_start, flags)
        active = list(names)
        pruned: list[str] = []
        if definition.prune_corr_threshold is not None:
            active, pruned = _prune(definition, panels, hist if not flags.future_pruning else dates)
        working = definition
        if pruned:
            working = definition.model_copy(
                update={
                    "components": [c for c in definition.components if c.component_id in active]
                }
            )
        if stacking:
            scores, weights = stack_at(working, panels, labels, hist, as_of, leaks=flags)
            fallback = False
        else:
            weights, fallback = compute_weights(
                working, panels, labels, hist, previous=previous, leaks=flags
            )
            rows = [
                _normalized_row(panels[cid].get(as_of, {}), definition, leaky_norm, cid)
                for cid in working.component_ids()
                if cid in panels
            ]
            wlist = [weights.get(cid, 0.0) for cid in working.component_ids()]
            scores = combine_at(working, rows, wlist) if rows else {}
        predictions[as_of] = scores
        turnover = weight_turnover(weights, previous)
        previous = dict(weights)
        weights_path.append(dict(weights))
        points.append(
            EnsemblePoint(
                as_of=as_of,
                coverage=bool(scores),
                weights=dict(weights),
                fallback_equal=fallback,
                regime=None if regimes is None else regimes.get(as_of),
                weight_turnover=turnover,
                pruned=pruned,
            )
        )

    scored: list[float] = []
    for i, as_of in enumerate(dates[:-1]):
        ic = spearman_ic(predictions.get(as_of, {}), labels.get(as_of, {}))
        points[i].ic = ic
        if ic is not None:
            scored.append(ic)

    component_ics: dict[str, float | None] = {}
    best_id: str | None = None
    best_ic: float | None = None
    for name in names:
        values = [
            ic
            for as_of in dates[:-1]
            if (ic := spearman_ic(panels.get(name, {}).get(as_of, {}), labels.get(as_of, {})))
            is not None
        ]
        mean = None if not values else sum(values) / len(values)
        component_ics[name] = mean
        if mean is not None and (best_ic is None or mean > best_ic):
            best_ic = mean
            best_id = name
    equal_panel = equal_weight_panel(panels, names, dates)
    equal_vals = [
        ic
        for as_of in dates[:-1]
        if (ic := spearman_ic(equal_panel.get(as_of, {}), labels.get(as_of, {}))) is not None
    ]
    equal_ic = None if not equal_vals else sum(equal_vals) / len(equal_vals)
    n_pred = sum(1 for p in points if p.coverage)
    mean = None if not scored else sum(scored) / len(scored)
    hit = None if not scored else sum(1 for v in scored if v > 0) / len(scored)
    cov = None if not points else n_pred / len(points)
    turns = [p.weight_turnover for p in points if p.weight_turnover is not None]
    mean_to = None if not turns else sum(turns) / len(turns)
    spread = _quantile_spread(predictions, labels, dates)
    cutoff = dates[-1]
    state = EnsembleState(
        ensemble_definition_id=f"{definition.ensemble_id}@{definition.version}",
        fit_timestamp=datetime.now(tz=UTC),
        training_start=dates[0],
        training_end=dates[-1],
        available_information_cutoff=cutoff,
        weights=dict(previous or {}),
        weight_policy=definition.weighting_policy.value,
        normalization_state=definition.normalization.value,
        hyperparameters={"window": definition.training_window, "l2": definition.l2},
        random_seed=definition.seed,
        dataset_snapshot=snapshot_id,
        config_hash=definition.identity_hash(),
    )
    last_preds = _last_predictions(state, dates[-1], predictions, panels, names, previous, regimes)
    status = CheckResult.NOT_TESTED if len(scored) < definition.min_obs else CheckResult.PASS
    if flags.full_sample_replay or flags.stacking_leak:
        status = CheckResult.FAIL
    result = EnsembleResult(
        n_predictions=n_pred,
        n_scored=len(scored),
        mean_ic=mean,
        hit_rate=hit,
        coverage=cov,
        mean_weight_turnover=mean_to,
        quantile_spread=spread,
        points=points,
        weights_path=weights_path,
        predictions=predictions,
        component_ics=component_ics,
        equal_weight_ic=equal_ic,
        best_component_id=best_id,
        best_component_ic=best_ic,
        final_state=state,
        last_predictions=last_preds,
        status=status,
        note=(
            "leaky: future or in-sample information used for weights or meta-model"
            if _leaky(flags)
            else "combine at T using components and weights available at T; label T→T+1 is not used"
        ),
    )
    return panels, labels, result


def _leaky(flags: EnsembleLeakFlags) -> bool:
    return any(
        (
            flags.future_weights,
            flags.future_correlation,
            flags.future_component_performance,
            flags.future_normalization,
            flags.future_meta_feature,
            flags.future_component_selection,
            flags.future_stacking,
            flags.future_pruning,
            flags.future_hyperparameter,
            flags.holdout_contaminated,
            flags.stacking_leak,
            flags.full_sample_replay,
            flags.future_covariance,
            flags.future_regime,
        )
    )


def _history_dates(
    dates: list[datetime],
    index: int,
    as_of: datetime,
    holdout_start: datetime | None,
    flags: EnsembleLeakFlags,
) -> list[datetime]:
    if (
        flags.future_weights
        or flags.future_component_performance
        or flags.future_correlation
        or flags.full_sample_replay
        or flags.stacking_leak
        or flags.future_stacking
    ):
        return list(dates)
    hist = dates[:index]
    if holdout_start is not None and not flags.holdout_contaminated:
        hist = [d for d in hist if d < holdout_start]
        if as_of >= holdout_start:
            return hist
    return hist


def _pooled_norm(panels: dict[str, Panel]) -> dict[str, tuple[float | None, float | None]]:
    return {cid: pooled_moments(panel) for cid, panel in panels.items()}


def _normalized_row(
    row: dict[str, float],
    definition: EnsembleDefinition,
    leaky: dict[str, tuple[float | None, float | None]] | None,
    component_id: str,
) -> dict[str, float]:
    mean = std = None
    if leaky is not None:
        mean, std = leaky.get(component_id, (None, None))
    method = definition.normalization
    if method is Normalization.RAW:
        return dict(row)
    return normalize_row(row, method, global_mean=mean, global_std=std)


def _prune(
    definition: EnsembleDefinition,
    panels: dict[str, Panel],
    hist: list[datetime],
) -> tuple[list[str], list[str]]:
    threshold = definition.prune_corr_threshold
    names = definition.component_ids()
    if threshold is None or len(names) < 2 or not hist:
        return names, []
    from quantlab.ensemble.diversity import pairwise_correlations

    report = pairwise_correlations(panels, hist, names)
    drop: set[str] = set()
    for pair in report.pairs:
        if pair.spearman is not None and abs(pair.spearman) > threshold:
            drop.add(sorted((pair.left, pair.right))[1])
    kept = [name for name in names if name not in drop]
    if not kept:
        raise EnsembleError("pruning removed every component")
    return kept, sorted(drop)


def _quantile_spread(predictions: Panel, labels: Panel, dates: list[datetime]) -> float | None:
    diffs: list[float] = []
    for as_of in dates[:-1]:
        scores = predictions.get(as_of, {})
        fwd = labels.get(as_of, {})
        keys = [k for k in scores if k in fwd]
        if len(keys) < 4:
            continue
        ordered = sorted(keys, key=lambda k: scores[k])
        mid = len(ordered) // 2
        low = sum(fwd[k] for k in ordered[:mid]) / mid
        high = sum(fwd[k] for k in ordered[mid:]) / (len(ordered) - mid)
        diffs.append(high - low)
    if not diffs:
        return None
    return sum(diffs) / len(diffs)


def _last_predictions(
    state: EnsembleState,
    as_of: datetime,
    predictions: Panel,
    panels: dict[str, Panel],
    names: list[str],
    weights: dict[str, float] | None,
    regimes: dict[datetime, str | None] | None,
) -> list[EnsemblePrediction]:
    scores = predictions.get(as_of, {})
    w = weights or {}
    out: list[EnsemblePrediction] = []
    for inst, value in scores.items():
        comps = {name: panels.get(name, {}).get(as_of, {}).get(inst, 0.0) for name in names}
        out.append(
            EnsemblePrediction(
                ensemble_state_id=state.config_hash,
                prediction_time=as_of,
                security_id=inst,
                component_predictions=comps,
                component_weights=dict(w),
                composite_score=value,
                normalization=state.normalization_state,
                regime_context=None if regimes is None else regimes.get(as_of),
                available_information_cutoff=state.available_information_cutoff,
            )
        )
    return out
