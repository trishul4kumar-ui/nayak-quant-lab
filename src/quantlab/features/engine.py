"""Point-in-time feature engine. Trailing windows on bars with available_time <= as_of."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from quantlab.core.identifiers import InstrumentId
from quantlab.data.fabric.types import FeatureStatus
from quantlab.domain.models import OHLCVBar
from quantlab.features.definition import (
    FeatureDefinition,
    FeatureOperator,
    MissingValuePolicy,
    NormalizationMethod,
)
from quantlab.features.normalize import apply_cross_section
from quantlab.features.operators import (
    close_to_high,
    close_to_low,
    dollar_turnover_ratio,
    high_low_range,
    price_field,
    rolling_mean,
    rolling_std_of_returns,
    trailing_return,
    trailing_zscore,
    volume_change,
)

Panel = dict[datetime, dict[str, float]]


class FeatureObservation(BaseModel):
    instrument: str
    as_of: datetime
    value: float | None
    available_time: datetime
    event_time: datetime
    missing: bool
    status: FeatureStatus
    note: str = ""


def pit_bars(series: list[OHLCVBar], as_of: datetime) -> list[OHLCVBar]:
    """Earliest-available print per event_time among bars knowable at as_of."""
    chosen: dict[datetime, OHLCVBar] = {}
    ordered = sorted(series, key=lambda b: (b.pit.available_time, b.pit.event_time))
    for bar in ordered:
        if bar.pit.available_time > as_of:
            continue
        event = bar.pit.event_time
        prev = chosen.get(event)
        if prev is None or bar.pit.available_time < prev.pit.available_time:
            chosen[event] = bar
    return sorted(chosen.values(), key=lambda b: b.pit.event_time)


def session_calendar(bars: dict[InstrumentId, list[OHLCVBar]]) -> list[datetime]:
    times: set[datetime] = set()
    for series in bars.values():
        for bar in series:
            times.add(bar.pit.event_time)
    return sorted(times)


def universe_present(
    bars: dict[InstrumentId, list[OHLCVBar]],
    as_of: datetime,
) -> list[str]:
    names: list[str] = []
    for inst, series in bars.items():
        if pit_bars(series, as_of):
            names.append(str(inst))
    return names


def compute_value(
    definition: FeatureDefinition,
    series: list[OHLCVBar],
    as_of: datetime,
) -> FeatureObservation:
    bars = pit_bars(series, as_of)
    inst = str(series[0].instrument) if series else ""
    if not bars:
        return FeatureObservation(
            instrument=inst,
            as_of=as_of,
            value=None,
            available_time=as_of,
            event_time=as_of,
            missing=True,
            status=FeatureStatus.MISSING_DATA,
            note="no PIT-available bars",
        )
    last = bars[-1]
    if last.pit.available_time > as_of:
        raise RuntimeError("pit_bars leaked a future print")
    value, status, note = _apply_operator(definition, bars)
    missing = value is None
    if missing and definition.missing_value_policy is MissingValuePolicy.ZERO:
        value = 0.0
        missing = False
        note = (note + "; filled zero").strip("; ")
    return FeatureObservation(
        instrument=str(last.instrument),
        as_of=as_of,
        value=value,
        available_time=last.pit.available_time,
        event_time=last.pit.event_time,
        missing=missing,
        status=status,
        note=note,
    )


def compute_panel(
    definition: FeatureDefinition,
    bars: dict[InstrumentId, list[OHLCVBar]],
    as_of_times: list[datetime] | None = None,
    names_at: dict[datetime, list[str]] | None = None,
) -> Panel:
    dates = as_of_times or session_calendar(bars)
    raw: dict[datetime, dict[str, float | None]] = {}
    for as_of in dates:
        allowed = None if names_at is None else set(names_at.get(as_of, []))
        row: dict[str, float | None] = {}
        for inst, series in bars.items():
            key = str(inst)
            if allowed is not None and key not in allowed:
                continue
            obs = compute_value(definition, series, as_of)
            if obs.available_time > as_of:
                raise RuntimeError("feature available_time exceeded decision_time")
            row[key] = obs.value
        raw[as_of] = row
    filled = _apply_missing_policy(raw, definition.missing_value_policy)
    panel: Panel = {}
    for as_of, row in filled.items():
        present = {k: v for k, v in row.items() if v is not None}
        if not present:
            continue
        if definition.normalization is not NormalizationMethod.NONE:
            present = apply_cross_section(present, definition.normalization)
        panel[as_of] = present
    return panel


def _apply_operator(
    definition: FeatureDefinition,
    bars: list[OHLCVBar],
) -> tuple[float | None, FeatureStatus, str]:
    op = definition.operator
    lookback = definition.lookback
    field = definition.price_field
    prices = [price_field(b, field) for b in bars]
    volumes = [float(b.volume) for b in bars]
    last = bars[-1]

    if op is FeatureOperator.NOT_IMPLEMENTED:
        return None, FeatureStatus.INVALID, definition.notes or "NOT_TESTED: data contract missing"
    if op is FeatureOperator.ROLLING_BETA:
        return None, FeatureStatus.INVALID, "NOT_TESTED: no bundled market index for beta"

    need = (
        lookback + 1
        if op in {FeatureOperator.TRAILING_RETURN, FeatureOperator.ROLLING_STD}
        else lookback
    )
    if op in {
        FeatureOperator.TRAILING_RETURN,
        FeatureOperator.ROLLING_MEAN,
        FeatureOperator.ROLLING_STD,
        FeatureOperator.ZSCORE_TS,
        FeatureOperator.VOLUME_ZSCORE,
        FeatureOperator.DISTANCE_FROM_MEAN,
        FeatureOperator.DOLLAR_TURNOVER_RATIO,
    } and len(bars) < max(need, 1):
        return None, FeatureStatus.INSUFFICIENT_HISTORY, f"need {need} sessions, have {len(bars)}"

    if op is FeatureOperator.TRAILING_RETURN:
        return trailing_return(prices, lookback), FeatureStatus.READY, ""
    if op is FeatureOperator.ROLLING_MEAN:
        return rolling_mean(prices, lookback), FeatureStatus.READY, ""
    if op is FeatureOperator.ROLLING_STD:
        return rolling_std_of_returns(prices, lookback), FeatureStatus.READY, ""
    if op is FeatureOperator.ZSCORE_TS:
        return trailing_zscore(prices, lookback), FeatureStatus.READY, ""
    if op is FeatureOperator.HIGH_LOW_RANGE:
        return high_low_range(last), FeatureStatus.READY, ""
    if op is FeatureOperator.CLOSE_TO_HIGH:
        return close_to_high(last), FeatureStatus.READY, ""
    if op is FeatureOperator.CLOSE_TO_LOW:
        return close_to_low(last), FeatureStatus.READY, ""
    if op is FeatureOperator.LAST_VOLUME:
        return float(last.volume), FeatureStatus.READY, "synthetic volume, not NSE ADV"
    if op is FeatureOperator.VOLUME_CHANGE:
        value = volume_change(volumes)
        status = FeatureStatus.READY if value is not None else FeatureStatus.INSUFFICIENT_HISTORY
        return value, status, "synthetic volume, not NSE ADV"
    if op is FeatureOperator.VOLUME_ZSCORE:
        value = trailing_zscore(volumes, lookback)
        return value, FeatureStatus.READY, "synthetic volume, not NSE ADV"
    if op is FeatureOperator.DISTANCE_FROM_MEAN:
        mean = rolling_mean(prices, lookback)
        if mean is None or mean <= 0:
            return None, FeatureStatus.INSUFFICIENT_HISTORY, ""
        return prices[-1] / mean - 1.0, FeatureStatus.READY, ""
    if op is FeatureOperator.DOLLAR_TURNOVER_RATIO:
        value = dollar_turnover_ratio(prices, volumes, lookback)
        return value, FeatureStatus.READY, "turnover proxy from synthetic dollar volume"
    raise ValueError(f"unsupported operator: {op}")


def _apply_missing_policy(
    raw: dict[datetime, dict[str, float | None]],
    policy: MissingValuePolicy,
) -> dict[datetime, dict[str, float | None]]:
    if policy is MissingValuePolicy.FORWARD_FILL:
        last: dict[str, float] = {}
        out: dict[datetime, dict[str, float | None]] = {}
        for as_of in sorted(raw):
            row: dict[str, float | None] = {}
            for key, value in raw[as_of].items():
                if value is not None:
                    last[key] = value
                    row[key] = value
                else:
                    row[key] = last.get(key)
            out[as_of] = row
        return out
    if policy is MissingValuePolicy.DROP:
        return {
            as_of: {k: v for k, v in row.items() if v is not None} for as_of, row in raw.items()
        }
    return raw
