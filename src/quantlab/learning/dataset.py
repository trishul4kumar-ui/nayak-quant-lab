"""PIT model dataset. Not a second data fabric. Missing is not zero."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.alpha.combinations import combine_panels
from quantlab.alpha.definition import get_alpha
from quantlab.core.errors import ModelError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.features.engine import Panel, compute_panel, session_calendar
from quantlab.features.registry import get_feature
from quantlab.labels.definition import resolve_label
from quantlab.labels.engine import compute_label, compute_label_panel
from quantlab.learning.definition import ModelDefinition
from quantlab.realtime_data.hashing import sha256


class ModelDataset(BaseModel):
    dates: list[datetime]
    feature_ids: list[str]
    features: dict[str, Panel] = Field(default_factory=dict)
    labels: Panel = Field(default_factory=dict)
    label_available_at: dict[datetime, dict[str, datetime]] = Field(default_factory=dict)
    alpha_panel: Panel = Field(default_factory=dict)
    snapshot_id: str = ""
    label_id: str = "forward_return_1"
    label_definition_hash: str = ""
    frequency: str = "1d"
    missing_policy: str = "drop"
    note: str = "features available at T; label T→T+1 known at T+1"


def build_dataset(
    model: ModelDefinition,
    bars: dict[InstrumentId, list[OHLCVBar]],
    dates: list[datetime] | None = None,
) -> ModelDataset:
    calendar = dates or session_calendar(bars)
    features: dict[str, Panel] = {}
    for fid in model.features:
        features[fid] = compute_panel(get_feature(fid), bars, calendar)
    label_definition = resolve_label(model.target)
    labels = compute_label_panel(label_definition, bars, calendar)
    availability: dict[datetime, dict[str, datetime]] = {}
    for as_of in calendar:
        row: dict[str, datetime] = {}
        for instrument, series in bars.items():
            observation = compute_label(label_definition, series, as_of)
            if observation.value is not None and observation.available_time is not None:
                row[str(instrument)] = observation.available_time
        if row:
            availability[as_of] = row
    alpha_panel: Panel = {}
    if model.alpha_id:
        alpha = get_alpha(model.alpha_id)
        panels = [compute_panel(get_feature(fid), bars, calendar) for fid in alpha.input_features]
        alpha_panel = combine_panels(panels, alpha.transformation)
    return ModelDataset(
        dates=calendar,
        feature_ids=list(model.features),
        features=features,
        labels=labels,
        label_available_at=availability,
        alpha_panel=alpha_panel,
        label_id=label_definition.label_id,
        label_definition_hash=sha256(label_definition.model_dump(mode="json")),
        missing_policy=model.missing_value_policy.value,
    )


def row_xy(
    dataset: ModelDataset,
    as_of: datetime,
    feature_ids: list[str] | None = None,
    *,
    label_as_feature: bool = False,
    training_cutoff: datetime | None = None,
) -> tuple[list[str], list[list[float]], list[float | None]]:
    """Cross-section at as_of. Drops names with any missing feature. Never fills 0."""
    names = feature_ids or dataset.feature_ids
    insts: set[str] | None = None
    for fid in names:
        panel = dataset.features.get(fid, {})
        row = panel.get(as_of, {})
        insts = set(row) if insts is None else insts & set(row)
    if not insts:
        return [], [], []
    labels = dataset.labels.get(as_of, {})
    instruments: list[str] = []
    xs: list[list[float]] = []
    ys: list[float | None] = []
    for inst in sorted(insts):
        vec: list[float] = []
        skip = False
        for fid in names:
            value = dataset.features.get(fid, {}).get(as_of, {}).get(inst)
            if value is None:
                skip = True
                break
            vec.append(float(value))
        if skip:
            continue
        y = labels.get(inst)
        available_at = dataset.label_available_at.get(as_of, {}).get(inst)
        cutoff = training_cutoff or as_of
        if y is not None and (available_at is None or available_at > cutoff):
            y = None
        if label_as_feature:
            if y is None:
                continue
            vec.append(float(y))
        instruments.append(inst)
        xs.append(vec)
        ys.append(None if y is None else float(y))
    return instruments, xs, ys


def labeled_rows(
    dataset: ModelDataset,
    dates: list[datetime],
    feature_ids: list[str] | None = None,
    *,
    label_as_feature: bool = False,
    training_cutoff: datetime | None = None,
) -> tuple[list[list[float]], list[float]]:
    xs: list[list[float]] = []
    ys: list[float] = []
    cutoff = training_cutoff or (max(dates) if dates else None)
    for as_of in dates:
        _insts, x_rows, y_rows = row_xy(
            dataset,
            as_of,
            feature_ids,
            label_as_feature=label_as_feature,
            training_cutoff=cutoff,
        )
        for x, y in zip(x_rows, y_rows, strict=True):
            if y is None:
                continue
            xs.append(x)
            ys.append(y)
    if not xs:
        raise ModelError("insufficient_history: no labeled training rows")
    return xs, ys
