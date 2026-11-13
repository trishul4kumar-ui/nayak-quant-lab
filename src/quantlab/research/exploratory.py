"""Explicit retrospective analysis of frozen REAL captures, never PIT certification.

The analytical clock below is a *model assumption*: an interval's OHLC facts are
indexed at its close. It is not a claim that this broker revision was historically
available then. These transient bars must not be imported into the verified PIT
store, used by validation, or presented as historically verified observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from quantlab.agents.hashing import digest
from quantlab.agents.repository import AgentRepository
from quantlab.app.market_backtest import FrozenMarketHistory
from quantlab.core.errors import DataIntegrityError
from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.domain.models import BarInterval, Instrument, OHLCVBar
from quantlab.realtime_data.candles import INTERVALS


@dataclass(frozen=True)
class ExploratoryFrame:
    histories: tuple[FrozenMarketHistory, ...]
    bars: dict[InstrumentId, list[OHLCVBar]]
    dates: tuple[datetime, ...]
    dropped_bars: tuple[int, ...]
    missing_volume: tuple[str, ...]

    @property
    def instruments(self) -> list[Instrument]:
        return [Instrument(id=key, name=key.symbol) for key in self.bars]

    @property
    def interval(self) -> str:
        return self.histories[0].interval

    @property
    def input_hash(self) -> str:
        return digest(
            {
                "tier": "EXPLORATORY",
                "histories": [h.content_hash for h in self.histories],
                "aligned_times": [d.isoformat() for d in self.dates],
            }
        )


def load_exploratory_frame(
    repository_path: Path,
    history_hashes: tuple[str, ...],
    *,
    minimum_bars: int = 3,
    start: datetime | None = None,
    end: datetime | None = None,
) -> ExploratoryFrame:
    """Load exact hashes; intersect actual timestamps, never zip unequal calendars."""
    if not history_hashes or len(history_hashes) > 64:
        raise DataIntegrityError("EXPLORATORY_HISTORY_SELECTION_REQUIRED: select 1–64 captures")
    if len(set(history_hashes)) != len(history_hashes):
        raise DataIntegrityError("DUPLICATE_HISTORY_SELECTION")
    if minimum_bars < 3:
        raise DataIntegrityError("EXPLORATORY_MINIMUM_HISTORY_INVALID")
    for value in (start, end):
        if value is not None and value.tzinfo is None:
            raise DataIntegrityError("EXPLORATORY_RANGE_CLOCK_REQUIRED")
    if start and end and start >= end:
        raise DataIntegrityError("EXPLORATORY_RANGE_INVALID")
    repository = AgentRepository(repository_path)
    try:
        try:
            histories = tuple(
                repository.get(h, FrozenMarketHistory).verified() for h in history_hashes
            )
        except KeyError as exc:
            raise DataIntegrityError(
                "FROZEN_HISTORY_NOT_FOUND: selected capture is unavailable"
            ) from exc
    finally:
        repository.close()
    histories = tuple(sorted(histories, key=lambda h: h.instrument))
    if len({h.instrument for h in histories}) != len(histories):
        raise DataIntegrityError(
            "DUPLICATE_INSTRUMENT_CAPTURE: choose exactly one version per symbol"
        )
    if len({h.interval for h in histories}) != 1:
        raise DataIntegrityError("INCOMPATIBLE_HISTORY_INTERVALS: capture the same interval")
    if any(h.captured_at > datetime.now(UTC) + timedelta(seconds=120) for h in histories):
        raise DataIntegrityError("HISTORY_CAPTURE_CLOCK_IN_FUTURE")
    duration = timedelta(seconds=INTERVALS[histories[0].interval])
    time_sets = [{bar.time.astimezone(UTC) for bar in h.candles} for h in histories]
    common = set.intersection(*time_sets)
    # Analysis cutoffs refer to interval closes, not raw provider bar starts.
    # A candle that starts at the cutoff contains later closing information.
    common = {
        time
        for time in common
        if (start is None or time + duration >= start) and (end is None or time + duration <= end)
    }
    if len(common) < minimum_bars:
        raise DataIntegrityError(
            f"INSUFFICIENT_ALIGNED_HISTORY: need {minimum_bars} common closed bars; "
            f"have {len(common)}. "
            "Capture compatible instruments over an overlapping range; no interpolation is applied."
        )
    if len(common) > 2000 or len(common) * len(histories) > 30000:
        raise DataIntegrityError(
            "EXPLORATORY_WORK_BUDGET_EXCEEDED: select an explicit shorter range "
            "(maximum 2000 aligned bars / 30000 instrument-bars per job)."
        )
    raw_dates = tuple(sorted(common))
    bars: dict[InstrumentId, list[OHLCVBar]] = {}
    missing_volume: list[str] = []
    for history in histories:
        instrument = InstrumentId.parse(history.instrument)
        if instrument.exchange not in {"NSE", "BSE"}:
            raise DataIntegrityError("UNSUPPORTED_HISTORY_VENUE")
        selected = [bar for bar in history.candles if bar.time.astimezone(UTC) in common]
        if any(bar.volume is None for bar in selected):
            missing_volume.append(history.instrument)
        # OHLCVBar requires volume. A missing volume is an unavailable capability,
        # not a zero observation: all volume-dependent work is rejected by callers.
        bars[instrument] = [
            OHLCVBar(
                instrument=instrument,
                pit=PointInTime(
                    event_time=bar.time + duration,
                    effective_time=bar.time + duration,
                    available_time=bar.time + duration,
                    ingestion_time=history.captured_at,
                ),
                interval=BarInterval.DAY if history.interval == "day" else BarInterval.MINUTE,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=0.0 if bar.volume is None else bar.volume,
                dataset_version=history.content_hash,
                source_id=history.source,
                session_date=bar.time.date().isoformat(),
                data_kind="REAL",
            )
            for bar in selected
        ]
    return ExploratoryFrame(
        histories=histories,
        bars=bars,
        dates=tuple(time + duration for time in raw_dates),
        dropped_bars=tuple(len(h.candles) - len(common) for h in histories),
        missing_volume=tuple(missing_volume),
    )
