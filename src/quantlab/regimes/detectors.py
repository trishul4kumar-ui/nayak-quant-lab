"""Rule-based regime detectors. Labels describe state; they are not forecasts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.domain.research import CheckResult
from quantlab.regimes.definition import RegimeModel
from quantlab.regimes.normalize import expanding_tercile, series_of
from quantlab.regimes.snapshot import StateSnapshot


class RegimeObservation(BaseModel):
    schema_version: str = "1"
    as_of: datetime
    hard_label: str | None = None
    probabilities: dict[str, float] = Field(default_factory=dict)
    confidence: float | None = None
    method: str
    retrospective: bool = False
    status: CheckResult = CheckResult.PASS
    note: str = "hard_label is a classification, not a prediction"


def classify_rules(model: RegimeModel, snapshots: list[StateSnapshot]) -> list[RegimeObservation]:
    if model.regime_model_id == "vol_tercile":
        buckets = expanding_tercile(series_of(snapshots, "realized_vol_20"), min_obs=model.min_obs)
        return _from_labels(snapshots, buckets, model.detector.value)
    if model.regime_model_id == "trend_sign":
        labels = _sign_labels(series_of(snapshots, "market_ew_return_20"), model.min_obs)
        return _from_labels(snapshots, labels, model.detector.value)
    if model.regime_model_id == "corr_tercile":
        buckets = expanding_tercile(
            series_of(snapshots, "avg_pairwise_corr"), min_obs=model.min_obs
        )
        return _from_labels(snapshots, buckets, model.detector.value)
    if model.regime_model_id == "vol_trend":
        vol = expanding_tercile(series_of(snapshots, "realized_vol_20"), min_obs=model.min_obs)
        trend = _sign_labels(series_of(snapshots, "market_ew_return_20"), model.min_obs)
        combined: list[str | None] = []
        for v, t in zip(vol, trend, strict=True):
            if v is None or t is None:
                combined.append(None)
            else:
                combined.append(f"{v}_{t}")
        return _from_labels(snapshots, combined, model.detector.value)
    raise KeyError(f"no rule detector for {model.regime_model_id}")


def _sign_labels(values: list[float | None], min_obs: int) -> list[str | None]:
    out: list[str | None] = []
    seen = 0
    for value in values:
        if value is None:
            out.append(None)
            continue
        seen += 1
        if seen < min_obs:
            out.append(None)
        else:
            out.append("up" if value >= 0 else "down")
    return out


def _from_labels(
    snapshots: list[StateSnapshot],
    labels: list[str | None],
    method: str,
) -> list[RegimeObservation]:
    rows: list[RegimeObservation] = []
    for snap, label in zip(snapshots, labels, strict=True):
        probs: dict[str, float] = {}
        if label is not None:
            probs[label] = 1.0
        rows.append(
            RegimeObservation(
                as_of=snap.as_of,
                hard_label=label,
                probabilities=probs,
                confidence=None if label is None else 1.0,
                method=method,
                status=CheckResult.NOT_TESTED if label is None else CheckResult.PASS,
                note=(
                    "insufficient history"
                    if label is None
                    else "rule-based hard assignment; not a forecast"
                ),
            )
        )
    return rows
