"""Prequential loop: predict → realize → score → update. Never fit-then-replay."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.adaptive.definition import AdaptationPolicy, AdaptiveModelDefinition
from quantlab.adaptive.drift import attach_drift, classify_drift
from quantlab.adaptive.learners import empty_state, predict, update_state
from quantlab.adaptive.state import AdaptiveModelState, ResetEvent, UpdateEvent
from quantlab.domain.research import CheckResult
from quantlab.features.engine import Panel
from quantlab.research.cross_section import spearman_ic


class PrequentialPoint(BaseModel):
    as_of: datetime
    ic: float | None = None
    n_updates_before_predict: int = 0
    coverage: bool = False


class PrequentialResult(BaseModel):
    schema_version: str = "1"
    n_predictions: int = 0
    n_scored: int = 0
    mean_ic: float | None = None
    hit_rate: float | None = None
    coverage: float | None = None
    points: list[PrequentialPoint] = Field(default_factory=list)
    updates: list[UpdateEvent] = Field(default_factory=list)
    resets: list[ResetEvent] = Field(default_factory=list)
    final_state: AdaptiveModelState | None = None
    weights_path: list[dict[str, float]] = Field(default_factory=list)
    predictions: dict[datetime, dict[str, float]] = Field(default_factory=dict)
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = "predict at T using outcomes available at T; label T→T+1 is not used"


def run_prequential(
    model: AdaptiveModelDefinition,
    panels: dict[str, Panel],
    labels: Panel,
    dates: list[datetime],
    *,
    regimes: dict[datetime, str | None] | None = None,
    leaky_full_sample: bool = False,
    update_before_predict: bool = False,
) -> PrequentialResult:
    if not dates:
        return PrequentialResult(note="empty calendar")
    state = empty_state(model, dates[0])
    regime_states: dict[str, AdaptiveModelState] = {}
    component_ics: dict[str, list[float]] = {alpha_id: [] for alpha_id in model.alpha_ids}
    leaky_ics = _all_component_ics(panels, labels, dates) if leaky_full_sample else None
    predictions: dict[datetime, dict[str, float]] = {}
    points: list[PrequentialPoint] = []
    updates: list[UpdateEvent] = []
    resets: list[ResetEvent] = []
    weights_path: list[dict[str, float]] = []

    for i, as_of in enumerate(dates):
        if update_before_predict:
            leaked = spearman_ic(panels[model.alpha_ids[0]].get(as_of, {}), labels.get(as_of, {}))
            if leaked is not None:
                state = update_state(model, state, ic=leaked, as_of=as_of)
        elif i > 0:
            prev = dates[i - 1]
            state, regime_states, component_ics = _realize(
                model,
                state,
                regime_states,
                component_ics,
                panels,
                predictions,
                labels,
                prev,
                as_of,
                regimes,
                updates,
                resets,
            )
        panels_at_t = {
            alpha_id: panels.get(alpha_id, {}).get(as_of, {}) for alpha_id in model.alpha_ids
        }
        active = _active_state(model, state, regime_states, as_of, regimes)
        ics_for_predict = leaky_ics if leaky_ics is not None else component_ics
        scores = predict(model, active, panels_at_t, ics_for_predict)
        state = active
        predictions[as_of] = scores
        if state.weights:
            weights_path.append(dict(state.weights))
        points.append(
            PrequentialPoint(
                as_of=as_of,
                n_updates_before_predict=state.n_updates,
                coverage=bool(scores),
            )
        )

    scored: list[float] = []
    for i, as_of in enumerate(dates[:-1]):
        ic = spearman_ic(predictions.get(as_of, {}), labels.get(as_of, {}))
        points[i].ic = ic
        if ic is not None:
            scored.append(ic)

    n_pred = sum(1 for p in points if p.coverage)
    mean = None if not scored else sum(scored) / len(scored)
    hit = None if not scored else sum(1 for v in scored if v > 0) / len(scored)
    cov = None if not points else n_pred / len(points)
    status = CheckResult.NOT_TESTED if len(scored) < model.min_obs else CheckResult.PASS
    return PrequentialResult(
        n_predictions=n_pred,
        n_scored=len(scored),
        mean_ic=mean,
        hit_rate=hit,
        coverage=cov,
        points=points,
        updates=updates,
        resets=resets,
        final_state=state,
        weights_path=weights_path,
        predictions=predictions,
        status=status,
        note=(
            "leaky: updated with label at T before predicting at T"
            if update_before_predict
            else "predict at T using outcomes available at T; label T→T+1 is not used"
        ),
    )


def _active_state(
    model: AdaptiveModelDefinition,
    state: AdaptiveModelState,
    regime_states: dict[str, AdaptiveModelState],
    as_of: datetime,
    regimes: dict[datetime, str | None] | None,
) -> AdaptiveModelState:
    if model.policy is not AdaptationPolicy.REGIME_CONDITIONAL or not regimes:
        return state
    label = regimes.get(as_of)
    if label is None:
        return empty_state(model, as_of)
    return regime_states.get(label) or empty_state(model, as_of)


def _realize(
    model: AdaptiveModelDefinition,
    state: AdaptiveModelState,
    regime_states: dict[str, AdaptiveModelState],
    component_ics: dict[str, list[float]],
    panels: dict[str, Panel],
    predictions: dict[datetime, dict[str, float]],
    labels: Panel,
    prev: datetime,
    as_of: datetime,
    regimes: dict[datetime, str | None] | None,
    updates: list[UpdateEvent],
    resets: list[ResetEvent],
) -> tuple[AdaptiveModelState, dict[str, AdaptiveModelState], dict[str, list[float]]]:
    fwd = labels.get(prev)
    if fwd is None:
        return state, regime_states, component_ics
    for alpha_id in model.alpha_ids:
        comp = spearman_ic(panels.get(alpha_id, {}).get(prev, {}), fwd)
        if comp is not None:
            component_ics.setdefault(alpha_id, []).append(comp)
    # Efficacy is the PIT IC of the underlying alpha, not of a gated-empty
    # prediction. Otherwise a stale-gate never accumulates history and never
    # turns back on after a silent period.
    pred_ic = spearman_ic(predictions.get(prev, {}), fwd)
    raw_ic = spearman_ic(panels.get(model.alpha_ids[0], {}).get(prev, {}), fwd)
    ic = pred_ic if pred_ic is not None else raw_ic
    if ic is None:
        return state, regime_states, component_ics
    if model.policy is AdaptationPolicy.REGIME_CONDITIONAL and regimes:
        label = regimes.get(prev)
        if label is None:
            return state, regime_states, component_ics
        target = regime_states.get(label) or empty_state(model, prev)
        target = _maybe_reset(model, update_state(model, target, ic=ic, as_of=prev), prev, resets)
        regime_states[label] = target
        state = target
    else:
        state = _maybe_reset(model, update_state(model, state, ic=ic, as_of=prev), prev, resets)
    updates.append(
        UpdateEvent(
            decision_time=as_of,
            outcome_as_of=prev,
            n_updates=state.n_updates,
            efficacy=state.efficacy,
        )
    )
    return state, regime_states, component_ics


def _maybe_reset(
    model: AdaptiveModelDefinition,
    state: AdaptiveModelState,
    as_of: datetime,
    resets: list[ResetEvent],
) -> AdaptiveModelState:
    report = classify_drift(state.ic_history, min_obs=max(model.min_obs * 2, 16))
    state = attach_drift(state, report)
    if model.policy is not AdaptationPolicy.DRIFT_TRIGGERED_REFIT:
        return state
    if report.status.value != "drift_detected":
        return state
    keep = state.ic_history[-model.min_obs :]
    keep_t = state.ic_times[-model.min_obs :]
    resets.append(
        ResetEvent(
            reset_time=as_of,
            reason="drift_detected",
            trigger_metric=report.statistic,
            threshold=3.0,
            old_n_updates=state.n_updates,
            new_n_updates=len(keep),
        )
    )
    return state.model_copy(
        update={
            "ic_history": keep,
            "ic_times": keep_t,
            "n_updates": len(keep),
            "last_reset": as_of,
            "note": "drift-triggered reset; future labels not used",
        }
    )


def _all_component_ics(
    panels: dict[str, Panel],
    labels: Panel,
    dates: list[datetime],
) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {alpha_id: [] for alpha_id in panels}
    for as_of in dates:
        fwd = labels.get(as_of)
        if fwd is None:
            continue
        for alpha_id, panel in panels.items():
            ic = spearman_ic(panel.get(as_of, {}), fwd)
            if ic is not None:
                out[alpha_id].append(ic)
    return out
