"""In-memory synthetic panels. Not NSE prices and not market evidence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np

from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.domain.models import BarInterval, OHLCVBar
from quantlab.features.engine import Panel


def weekday_sessions(start: datetime, n_sessions: int) -> list[datetime]:
    days: list[datetime] = []
    cursor = start
    while len(days) < n_sessions:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor = cursor + timedelta(days=1)
    return days


def _bar(
    instrument: InstrumentId,
    day: datetime,
    close: float,
    volume: float,
    available: datetime | None = None,
) -> OHLCVBar:
    when = available or day
    pit = PointInTime(
        event_time=day,
        effective_time=day,
        available_time=when,
        ingestion_time=when,
    )
    return OHLCVBar(
        instrument=instrument,
        pit=pit,
        interval=BarInterval.DAY,
        open=close,
        high=close * 1.01,
        low=close * 0.99,
        close=close,
        volume=volume,
    )


def planted_volume_predicts_return(
    n_names: int = 12,
    n_sessions: int = 50,
    seed: int = 1,
    beta: float = 0.02,
) -> dict[InstrumentId, list[OHLCVBar]]:
    """Volume at T is planted to predict the next-session return only."""
    rng = np.random.default_rng(seed)
    start = datetime(2024, 1, 2, 10, 0, tzinfo=UTC)
    sessions = weekday_sessions(start, n_sessions)
    names = [InstrumentId(exchange="NSE", symbol=f"P{i:02d}") for i in range(n_names)]
    prices = [100.0 + i for i in range(n_names)]
    prev_scores = np.zeros(n_names)
    out: dict[InstrumentId, list[OHLCVBar]] = {inst: [] for inst in names}
    for day in sessions:
        scores = rng.normal(0.0, 1.0, size=n_names)
        noise = rng.normal(0.0, 0.001, size=n_names)
        for i, inst in enumerate(names):
            ret = float(beta * prev_scores[i] + noise[i])
            prices[i] *= 1.0 + ret
            volume = 1_000_000.0 * (2.0 + float(scores[i]))
            out[inst].append(_bar(inst, day, prices[i], max(volume, 1.0)))
        prev_scores = scores
    return out


def null_independent_bars(
    n_names: int = 10,
    n_sessions: int = 50,
    seed: int = 2,
) -> dict[InstrumentId, list[OHLCVBar]]:
    rng = np.random.default_rng(seed)
    start = datetime(2024, 1, 2, 10, 0, tzinfo=UTC)
    sessions = weekday_sessions(start, n_sessions)
    names = [InstrumentId(exchange="NSE", symbol=f"N{i:02d}") for i in range(n_names)]
    prices = [100.0] * n_names
    out: dict[InstrumentId, list[OHLCVBar]] = {inst: [] for inst in names}
    for day in sessions:
        for i, inst in enumerate(names):
            prices[i] *= 1.0 + float(rng.normal(0.0, 0.01))
            volume = float(rng.uniform(5e5, 1.5e6))
            out[inst].append(_bar(inst, day, prices[i], volume))
    return out


def continuation_ar1_bars(
    n_names: int = 8,
    n_sessions: int = 60,
    seed: int = 3,
    phi: float = 0.6,
) -> dict[InstrumentId, list[OHLCVBar]]:
    rng = np.random.default_rng(seed)
    start = datetime(2024, 1, 2, 10, 0, tzinfo=UTC)
    sessions = weekday_sessions(start, n_sessions)
    names = [InstrumentId(exchange="NSE", symbol=f"C{i:02d}") for i in range(n_names)]
    prices = [100.0 + 5 * i for i in range(n_names)]
    prev = rng.normal(0.0, 0.01, size=n_names)
    out: dict[InstrumentId, list[OHLCVBar]] = {inst: [] for inst in names}
    for day in sessions:
        shock = rng.normal(0.0, 0.005, size=n_names)
        prev = phi * prev + shock
        for i, inst in enumerate(names):
            prices[i] *= 1.0 + float(prev[i])
            out[inst].append(_bar(inst, day, prices[i], 1_000_000.0))
    return out


def leaky_forward_panel(label: Panel) -> Panel:
    """Adversarial feature equal to the forward label (look-ahead)."""
    return {as_of: dict(row) for as_of, row in label.items()}


def permute_panel(panel: Panel, seed: int = 0) -> Panel:
    rng = np.random.default_rng(seed)
    out: Panel = {}
    for as_of, row in panel.items():
        keys = list(row.keys())
        values = [row[k] for k in keys]
        rng.shuffle(values)
        out[as_of] = {keys[i]: float(values[i]) for i in range(len(keys))}
    return out
