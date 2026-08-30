"""Classify snapshots with a versioned regime model. One engine, several detectors."""

from __future__ import annotations

from quantlab.core.errors import RegimeError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.regimes.change_points import ChangePointReport, cusum_flags
from quantlab.regimes.clustering import classify_clusters
from quantlab.regimes.definition import DetectorKind, RegimeModel
from quantlab.regimes.detectors import RegimeObservation, classify_rules
from quantlab.regimes.hmm import classify_hmm
from quantlab.regimes.snapshot import StateSnapshot, compute_snapshot_panel


def compute_state_panel(
    bars: dict[InstrumentId, list[OHLCVBar]],
    lookback: int = 20,
) -> list[StateSnapshot]:
    return compute_snapshot_panel(bars, lookback=lookback)


def classify(
    model: RegimeModel,
    snapshots: list[StateSnapshot],
    *,
    predictive: bool = True,
) -> list[RegimeObservation]:
    kind = model.detector
    if kind is DetectorKind.RULE:
        return classify_rules(model, snapshots)
    if kind is DetectorKind.HMM_FILTER:
        return classify_hmm(model, snapshots, predictive=True)
    if kind is DetectorKind.HMM_SMOOTH:
        return classify_hmm(model, snapshots, predictive=predictive)
    if kind is DetectorKind.CLUSTER_WALK_FORWARD:
        return classify_clusters(model, snapshots, predictive=True)
    if kind is DetectorKind.CLUSTER_FULL_SAMPLE:
        return classify_clusters(model, snapshots, predictive=predictive)
    if kind is DetectorKind.CHANGE_POINT:
        raise RegimeError(
            "change-point detector emits flags, not regime labels; use detect_changes"
        )
    if kind is DetectorKind.NOT_IMPLEMENTED:
        raise RegimeError(f"{model.regime_model_id} is NOT_IMPLEMENTED")
    raise RegimeError(f"unsupported detector {kind}")


def detect_changes(snapshots: list[StateSnapshot], threshold: float = 3.0) -> ChangePointReport:
    return cusum_flags(snapshots, threshold=threshold)
