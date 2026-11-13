"""Shared research bar source: selected verified REAL dataset, fixtures only in tests."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.identifiers import InstrumentId
from quantlab.data.fabric.layout import resolve_fabric_root
from quantlab.data.policy import fixtures_enabled
from quantlab.domain.models import Instrument, OHLCVBar


class ResearchBarProvider:
    def __init__(self, n_days: int = 80) -> None:
        if fixtures_enabled():
            from quantlab.data.providers.memory import MemoryBarProvider

            provider = MemoryBarProvider(n_days=n_days)
            self._bars = provider.all_bars()
            self._instruments = provider.get_instruments()
            self.data_kind = "synthetic"
            self.source = "memory_synthetic_nse"
        else:
            from quantlab.research.pipeline import load_real_frame

            frame = load_real_frame(fabric_root=resolve_fabric_root(), n_days=n_days)
            self._bars, self._instruments = frame.bars, frame.instruments
            self.data_kind, self.source = frame.record.data_kind.value, frame.record.source

    def get_instruments(self) -> list[Instrument]:
        return list(self._instruments)

    def all_bars(self) -> dict[InstrumentId, list[OHLCVBar]]:
        return {key: list(series) for key, series in self._bars.items()}

    def get_bars(self, instrument: InstrumentId, start: datetime, end: datetime) -> list[OHLCVBar]:
        return [bar for bar in self._bars[instrument] if start <= bar.pit.event_time <= end]
