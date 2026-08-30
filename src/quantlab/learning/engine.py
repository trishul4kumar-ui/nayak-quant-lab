"""Statistical learning engine. Reuses feature/label/regime engines. No second backtester."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.errors import ModelError, RegimeError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.features.engine import Panel, session_calendar
from quantlab.learning.dataset import ModelDataset, build_dataset
from quantlab.learning.definition import ModelDefinition
from quantlab.learning.walkforward import LeakFlags, WalkForwardResult, run_walkforward
from quantlab.regimes.definition import DetectorKind
from quantlab.regimes.engine import classify, compute_state_panel
from quantlab.regimes.registry import get_regime_model


def run_learning(
    model: ModelDefinition,
    bars: dict[InstrumentId, list[OHLCVBar]],
    *,
    leaks: LeakFlags | None = None,
    snapshot_id: str = "",
    predictive: bool = True,
) -> tuple[ModelDataset, Panel, WalkForwardResult, dict[datetime, str | None] | None]:
    dates = session_calendar(bars)
    dataset = build_dataset(model, bars, dates)
    regimes = None
    if model.regime_model_id:
        regimes = regime_labels(bars, model.regime_model_id, predictive=predictive)
    predictions, result = run_walkforward(model, dataset, leaks=leaks, snapshot_id=snapshot_id)
    return dataset, predictions, result, regimes


def regime_labels(
    bars: dict[InstrumentId, list[OHLCVBar]],
    regime_model_id: str,
    *,
    predictive: bool = True,
) -> dict[datetime, str | None]:
    model = get_regime_model(regime_model_id)
    if predictive and model.detector in {DetectorKind.HMM_SMOOTH, DetectorKind.CLUSTER_FULL_SAMPLE}:
        raise ModelError("smoothed or full-sample regime labels are not a predictive model feature")
    try:
        observations = classify(model, compute_state_panel(bars), predictive=predictive)
    except RegimeError as exc:
        raise ModelError(str(exc)) from exc
    return {row.as_of: row.hard_label for row in observations}
