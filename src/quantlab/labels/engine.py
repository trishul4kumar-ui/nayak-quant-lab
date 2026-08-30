"""Forward labels from PIT-available future bars. label_end > decision_time."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.features.engine import Panel, pit_bars, session_calendar
from quantlab.features.operators import price_field
from quantlab.labels.definition import LabelDefinition, LabelKind
from quantlab.math.metrics import max_drawdown, realized_vol, simple_returns


class LabelObservation(BaseModel):
    instrument: str
    decision_time: datetime
    horizon: int
    end_time: datetime | None
    value: float | None
    available_time: datetime | None
    missing: bool
    note: str = ""


def compute_label(
    definition: LabelDefinition,
    series: list[OHLCVBar],
    decision_time: datetime,
) -> LabelObservation:
    if definition.kind is LabelKind.FORWARD_EXCESS_RETURN and not definition.benchmark:
        return LabelObservation(
            instrument=str(series[0].instrument) if series else "",
            decision_time=decision_time,
            horizon=definition.horizon,
            end_time=None,
            value=None,
            available_time=None,
            missing=True,
            note="NOT_TESTED: no PIT benchmark (cash/index not invented)",
        )
    if not series:
        return LabelObservation(
            instrument="",
            decision_time=decision_time,
            horizon=definition.horizon,
            end_time=None,
            value=None,
            available_time=None,
            missing=True,
            note="empty series",
        )
    as_of = max(bar.pit.available_time for bar in series)
    bars = pit_bars(series, as_of)
    times = [b.pit.event_time for b in bars]
    inst = str(bars[0].instrument) if bars else ""
    if decision_time not in times:
        return LabelObservation(
            instrument=inst,
            decision_time=decision_time,
            horizon=definition.horizon,
            end_time=None,
            value=None,
            available_time=None,
            missing=True,
            note="decision_time not on the instrument calendar",
        )
    i = times.index(decision_time)
    j = i + definition.horizon
    if j >= len(bars):
        return LabelObservation(
            instrument=inst,
            decision_time=decision_time,
            horizon=definition.horizon,
            end_time=None,
            value=None,
            available_time=None,
            missing=True,
            note="insufficient future bars",
        )
    start = bars[i]
    end = bars[j]
    if end.pit.event_time <= decision_time:
        raise RuntimeError("label end_time must be after decision_time")
    path = bars[i : j + 1]
    prices = [price_field(b, definition.price_field) for b in path]
    value, note = _label_value(definition, prices)
    return LabelObservation(
        instrument=str(start.instrument),
        decision_time=decision_time,
        horizon=definition.horizon,
        end_time=end.pit.event_time,
        value=value,
        available_time=end.pit.available_time,
        missing=value is None,
        note=note,
    )


def compute_label_panel(
    definition: LabelDefinition,
    bars: dict[InstrumentId, list[OHLCVBar]],
    decision_times: list[datetime] | None = None,
) -> Panel:
    dates = decision_times or session_calendar(bars)
    panel: Panel = {}
    for as_of in dates:
        row: dict[str, float] = {}
        for inst, series in bars.items():
            obs = compute_label(definition, series, as_of)
            if obs.end_time is not None and obs.end_time <= as_of:
                raise RuntimeError("label leaked into decision_time")
            if obs.value is not None:
                row[str(inst)] = obs.value
        if row:
            panel[as_of] = row
    return panel


def _label_value(definition: LabelDefinition, prices: list[float]) -> tuple[float | None, str]:
    if len(prices) < 2 or prices[0] <= 0:
        return None, "non-positive start price"
    fwd = prices[-1] / prices[0] - 1.0
    if definition.kind is LabelKind.FORWARD_RETURN:
        return fwd, ""
    if definition.kind is LabelKind.FORWARD_BINARY_DIRECTION:
        return (1.0 if fwd > 0 else 0.0), ""
    if definition.kind is LabelKind.FORWARD_VOLATILITY:
        return realized_vol(simple_returns(prices)), ""
    if definition.kind is LabelKind.FORWARD_DRAWDOWN:
        return max_drawdown(prices), ""
    if definition.kind is LabelKind.FORWARD_EXCESS_RETURN:
        return None, "NOT_TESTED: excess return requires a PIT benchmark"
    raise ValueError(f"unsupported label kind: {definition.kind}")
