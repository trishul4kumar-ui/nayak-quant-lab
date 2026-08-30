"""PIT learners. Predict with state through T-1; never infer sign from the future."""

from __future__ import annotations

from datetime import datetime

from quantlab.adaptive.definition import AdaptiveModelDefinition, LearnerKind
from quantlab.adaptive.ensembles import constrain_weights
from quantlab.adaptive.ewma import effective_sample_size, ewma_mean, ewma_weights
from quantlab.adaptive.state import AdaptiveModelState, DriftStatus
from quantlab.alpha.combinations import weighted_zscore
from quantlab.domain.research import CheckResult
from quantlab.features.engine import Panel


def history_ics(state: AdaptiveModelState, window: int | None) -> list[float]:
    if window is None or window <= 0:
        return list(state.ic_history)
    return state.ic_history[-window:]


def estimate_efficacy(model: AdaptiveModelDefinition, state: AdaptiveModelState) -> float | None:
    kind = model.learner
    if kind is LearnerKind.STATIC:
        return None
    if kind is LearnerKind.BAYESIAN_HIT:
        total = state.posterior_a + state.posterior_b
        return None if total <= 0 else state.posterior_a / total
    rolling = kind in {LearnerKind.ROLLING_IC, LearnerKind.IC_WEIGHTED_ENSEMBLE}
    series = history_ics(state, model.window if rolling else None)
    if len(series) < model.min_obs:
        return None
    if kind is LearnerKind.EWMA_IC:
        return ewma_mean(series, model.half_life or 10.0)
    return sum(series) / len(series)


def component_mean_ics(
    model: AdaptiveModelDefinition,
    component_ics: dict[str, list[float]],
) -> dict[str, float]:
    window = model.window if model.learner is LearnerKind.IC_WEIGHTED_ENSEMBLE else None
    out: dict[str, float] = {}
    for alpha_id in model.alpha_ids:
        series = component_ics.get(alpha_id, [])
        if window is not None:
            series = series[-window:]
        if len(series) < model.min_obs:
            out[alpha_id] = 0.0
        else:
            out[alpha_id] = max(sum(series) / len(series), 0.0)
    return out


def predict(
    model: AdaptiveModelDefinition,
    state: AdaptiveModelState,
    panels_at_t: dict[str, dict[str, float]],
    component_ics: dict[str, list[float]] | None = None,
) -> dict[str, float]:
    """Scores at T using parameters estimated from outcomes already available at T."""
    if model.learner is LearnerKind.IC_WEIGHTED_ENSEMBLE:
        means = component_mean_ics(model, component_ics or {})
        weights, _fallback = constrain_weights(means, model)
        state.weights = weights
        rows = [panels_at_t[alpha_id] for alpha_id in model.alpha_ids if alpha_id in panels_at_t]
        wlist = [weights[alpha_id] for alpha_id in model.alpha_ids if alpha_id in panels_at_t]
        if len(rows) != len(model.alpha_ids):
            return {}
        return weighted_zscore(rows, wlist)
    alpha_id = model.alpha_ids[0]
    scores = panels_at_t.get(alpha_id, {})
    if model.learner is LearnerKind.STATIC:
        return dict(scores)
    efficacy = estimate_efficacy(model, state)
    state.efficacy = efficacy
    if model.learner is LearnerKind.BAYESIAN_HIT:
        if efficacy is None or efficacy <= 0.5:
            return {}
        return dict(scores)
    if efficacy is None or efficacy <= 0.0:
        return {}
    return dict(scores)


def update_state(
    model: AdaptiveModelDefinition,
    state: AdaptiveModelState,
    *,
    ic: float,
    as_of: datetime,
) -> AdaptiveModelState:
    history = list(state.ic_history) + [ic]
    times = list(state.ic_times) + [as_of]
    a = state.posterior_a + (1.0 if ic > 0 else 0.0)
    b = state.posterior_b + (0.0 if ic > 0 else 1.0)
    ess = None
    if model.learner is LearnerKind.EWMA_IC and history:
        ess = effective_sample_size(ewma_weights(len(history), model.half_life or 10.0))
    note = ""
    if ess is not None and ess < model.min_ess:
        note = f"EWMA ESS={ess:.2f} below min_ess={model.min_ess}"
    updated = state.model_copy(
        update={
            "as_of": as_of,
            "n_updates": state.n_updates + 1,
            "ic_history": history,
            "ic_times": times,
            "posterior_a": a,
            "posterior_b": b,
            "ess": ess,
            "status": CheckResult.PASS,
            "note": note,
        }
    )
    updated.efficacy = estimate_efficacy(model, updated)
    return updated


def empty_state(model: AdaptiveModelDefinition, as_of: datetime) -> AdaptiveModelState:
    return AdaptiveModelState(
        as_of=as_of,
        model_id=model.adaptive_model_id,
        drift_status=DriftStatus.INSUFFICIENT_DATA,
        status=CheckResult.NOT_TESTED,
        note="no updates yet",
    )


def blend_panels(panels: dict[str, Panel], weights: dict[str, float]) -> Panel:
    dates: set[datetime] | None = None
    for panel in panels.values():
        dates = set(panel) if dates is None else dates & set(panel)
    if not dates:
        return {}
    out: Panel = {}
    names = [alpha_id for alpha_id in weights if alpha_id in panels]
    wlist = [weights[alpha_id] for alpha_id in names]
    for as_of in sorted(dates):
        rows = [panels[alpha_id][as_of] for alpha_id in names]
        out[as_of] = weighted_zscore(rows, wlist)
    return out
