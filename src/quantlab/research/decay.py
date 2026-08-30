"""Signal decay. Holding-period diagnostics, not optimization."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar, Signal
from quantlab.research.cross_section import spearman_ic


class DecayPoint(BaseModel):
    horizon: int
    mean_ic: float | None
    n: int


class DecayReport(BaseModel):
    schema_version: str = "1"
    points: list[DecayPoint] = Field(default_factory=list)
    note: str = "decay of rank IC vs subsequent close-to-close returns"


def signal_decay(
    bars: dict[InstrumentId, list[OHLCVBar]],
    signals_by_date: dict[datetime, list[Signal]],
    horizons: tuple[int, ...] = (1, 2, 3, 5),
) -> DecayReport:
    closes: dict[str, dict[datetime, float]] = {}
    calendars: dict[str, list[datetime]] = {}
    for inst, series in bars.items():
        ordered = sorted(series, key=lambda b: b.pit.event_time)
        calendars[str(inst)] = [b.pit.event_time for b in ordered]
        closes[str(inst)] = {b.pit.event_time: b.close for b in ordered}

    points: list[DecayPoint] = []
    for h in horizons:
        ics: list[float] = []
        for as_of, signals in signals_by_date.items():
            scores = {str(s.instrument): s.score for s in signals}
            fwd: dict[str, float] = {}
            for key, cal in calendars.items():
                if as_of not in cal:
                    continue
                i = cal.index(as_of)
                if i + h >= len(cal):
                    continue
                p0 = closes[key][as_of]
                p1 = closes[key][cal[i + h]]
                if p0 > 0:
                    fwd[key] = p1 / p0 - 1.0
            ic = spearman_ic(scores, fwd)
            if ic is not None:
                ics.append(ic)
        points.append(
            DecayPoint(
                horizon=h,
                mean_ic=None if not ics else sum(ics) / len(ics),
                n=len(ics),
            )
        )
    return DecayReport(points=points)
