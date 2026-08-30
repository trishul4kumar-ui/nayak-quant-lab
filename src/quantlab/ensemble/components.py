"""Resolve ALPHA / MODEL / ADAPTIVE / FACTOR panels. Components keep independent identity."""

from __future__ import annotations

from datetime import datetime

from quantlab.adaptive.engine import compute_alpha_panel, regime_labels, run_adaptive
from quantlab.core.errors import AdaptiveError, EnsembleError, ModelError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.ensemble.combine import signed_row
from quantlab.ensemble.definition import ComponentType, EnsembleComponent, EnsembleDefinition
from quantlab.features.engine import Panel, session_calendar


def resolve_component_panels(
    definition: EnsembleDefinition,
    bars: dict[InstrumentId, list[OHLCVBar]],
    dates: list[datetime] | None = None,
    *,
    overrides: dict[str, Panel] | None = None,
) -> dict[str, Panel]:
    calendar = dates or session_calendar(bars)
    out: dict[str, Panel] = {}
    for item in definition.components:
        if overrides is not None and item.component_id in overrides:
            panel = overrides[item.component_id]
        else:
            panel = _resolve_one(item, bars, calendar)
        signed: Panel = {}
        for as_of, row in panel.items():
            signed[as_of] = signed_row(row, item.expected_direction)
        out[item.component_id] = signed
    return out


def _resolve_one(
    item: EnsembleComponent,
    bars: dict[InstrumentId, list[OHLCVBar]],
    dates: list[datetime],
) -> Panel:
    kind = item.component_type
    if kind is ComponentType.ALPHA:
        return compute_alpha_panel(item.component_id, bars, dates)
    if kind is ComponentType.FACTOR_SIGNAL:
        from quantlab.factors.engine import compute_factor_panel
        from quantlab.factors.registry import get_factor

        panel, _obs = compute_factor_panel(get_factor(item.component_id), bars, dates)
        return panel
    if kind is ComponentType.MODEL or kind is ComponentType.REGIME_CONDITIONED_MODEL:
        from quantlab.learning.engine import run_learning
        from quantlab.learning.registry import get_model

        try:
            _dataset, predictions, _wf, _reg = run_learning(get_model(item.component_id), bars)
        except (ModelError, KeyError) as exc:
            raise EnsembleError(f"incompatible component {item.component_id}: {exc}") from exc
        return predictions
    if kind is ComponentType.ADAPTIVE_MODEL:
        from quantlab.adaptive.registry import get_adaptive_model

        try:
            _panels, _labels, result = run_adaptive(get_adaptive_model(item.component_id), bars)
        except (AdaptiveError, KeyError) as exc:
            raise EnsembleError(f"incompatible component {item.component_id}: {exc}") from exc
        return result.predictions
    raise EnsembleError(f"unsupported component type {kind}")


def predictive_regimes(
    bars: dict[InstrumentId, list[OHLCVBar]],
    regime_model_id: str,
    *,
    predictive: bool = True,
) -> dict[datetime, str | None]:
    try:
        return regime_labels(bars, regime_model_id, predictive=predictive)
    except AdaptiveError as exc:
        raise EnsembleError(str(exc)) from exc
