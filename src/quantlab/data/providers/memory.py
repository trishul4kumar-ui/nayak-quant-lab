"""Deterministic synthetic NSE-like daily bars. No network, no credentials."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.domain.models import BarInterval, Instrument, OHLCVBar

SEED_NAMES = ("RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK")


class MemoryBarProvider:
    def __init__(
        self,
        n_days: int = 80,
        start: datetime | None = None,
        names: tuple[str, ...] = SEED_NAMES,
    ) -> None:
        self._start = start or datetime(2024, 1, 2, 10, 0, tzinfo=UTC)
        self._n_days = n_days
        self._instruments = [
            Instrument(id=InstrumentId(exchange="NSE", symbol=name), name=name) for name in names
        ]
        self._bars = {inst.id: self._series(inst.id, i) for i, inst in enumerate(self._instruments)}

    def get_instruments(self) -> list[Instrument]:
        return list(self._instruments)

    def get_bars(self, instrument: InstrumentId, start: datetime, end: datetime) -> list[OHLCVBar]:
        return [b for b in self._bars[instrument] if start <= b.pit.event_time <= end]

    def all_bars(self) -> dict[InstrumentId, list[OHLCVBar]]:
        return {k: list(v) for k, v in self._bars.items()}

    def _series(self, instrument: InstrumentId, salt: int) -> list[OHLCVBar]:
        bars: list[OHLCVBar] = []
        price = 100.0 + 10 * salt
        # Distinct drifts so cross-sectional momentum is not degenerate.
        daily = 0.001 + 0.0015 * salt
        for i in range(self._n_days):
            day = self._start + timedelta(days=i)
            if day.weekday() >= 5:
                continue
            open_px = price
            close = price * (1.0 + daily + 0.004 * ((i + salt) % 7 - 3) / 3.0)
            high = max(open_px, close) * 1.01
            low = min(open_px, close) * 0.99
            pit = PointInTime(
                event_time=day,
                effective_time=day,
                available_time=day,
                ingestion_time=day,
            )
            bars.append(
                OHLCVBar(
                    instrument=instrument,
                    pit=pit,
                    interval=BarInterval.DAY,
                    open=open_px,
                    high=high,
                    low=low,
                    close=close,
                    volume=1_000_000 + 1000 * i,
                )
            )
            price = close
        return bars
