"""Adaptive engine. Reuses feature/alpha/label/regime engines. No second backtester."""

from __future__ import annotations

from datetime import datetime

from quantlab.adaptive.definition import AdaptiveModelDefinition
from quantlab.adaptive.prequential import PrequentialResult, run_prequential
from quantlab.alpha.combinations import combine_panels
from quantlab.alpha.definition import get_alpha
from quantlab.core.errors import AdaptiveError, RegimeError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.features.engine import Panel, compute_panel, session_calendar
from quantlab.features.registry import get_feature
from quantlab.labels.definition import forward_return
from quantlab.labels.engine import compute_label_panel
from quantlab.regimes.definition import DetectorKind
from quantlab.regimes.engine import classify, compute_state_panel
from quantlab.regimes.registry import get_regime_model


def compute_alpha_panel(
    alpha_id: str,
    bars: dict[InstrumentId, list[OHLCVBar]],
    dates: list[datetime] | None = None,
) -> Panel:
    alpha = get_alpha(alpha_id)
    calendar = dates or session_calendar(bars)
    panels = [compute_panel(get_feature(fid), bars, calendar) for fid in alpha.input_features]
    return combine_panels(panels, alpha.transformation)


def compute_label_panel_1(
    bars: dict[InstrumentId, list[OHLCVBar]],
    dates: list[datetime],
) -> Panel:
    return compute_label_panel(forward_return(1), bars, dates)


def regime_labels(
    bars: dict[InstrumentId, list[OHLCVBar]],
    regime_model_id: str,
    *,
    predictive: bool = True,
) -> dict[datetime, str | None]:
    model = get_regime_model(regime_model_id)
    if predictive and model.detector in {DetectorKind.HMM_SMOOTH, DetectorKind.CLUSTER_FULL_SAMPLE}:
        raise AdaptiveError(
            "smoothed or full-sample regime labels are not a predictive adaptive feature"
        )
    try:
        observations = classify(model, compute_state_panel(bars), predictive=predictive)
    except RegimeError as exc:
        raise AdaptiveError(str(exc)) from exc
    return {row.as_of: row.hard_label for row in observations}


def run_adaptive(
    model: AdaptiveModelDefinition,
    bars: dict[InstrumentId, list[OHLCVBar]],
    *,
    leaky_full_sample: bool = False,
    update_before_predict: bool = False,
    predictive: bool = True,
) -> tuple[dict[str, Panel], Panel, PrequentialResult]:
    dates = session_calendar(bars)
    panels = {alpha_id: compute_alpha_panel(alpha_id, bars, dates) for alpha_id in model.alpha_ids}
    labels = compute_label_panel_1(bars, dates)
    regimes = None
    if model.regime_model_id:
        regimes = regime_labels(bars, model.regime_model_id, predictive=predictive)
    result = run_prequential(
        model,
        panels,
        labels,
        dates,
        regimes=regimes,
        leaky_full_sample=leaky_full_sample,
        update_before_predict=update_before_predict,
    )
    return panels, labels, result
