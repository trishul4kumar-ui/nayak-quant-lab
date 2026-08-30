"""MarketDataProvider over the PIT store. as_of is mandatory."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.identifiers import InstrumentId
from quantlab.data.fabric.store import PitStore
from quantlab.domain.models import Instrument, OHLCVBar


class FabricBarProvider:
    def __init__(
        self,
        store: PitStore,
        *,
        as_of: datetime,
        instruments: list[Instrument],
    ) -> None:
        self._store = store
        self._as_of = as_of
        self._instruments = instruments

    def get_instruments(self) -> list[Instrument]:
        return list(self._instruments)

    def get_bars(self, instrument: InstrumentId, start: datetime, end: datetime) -> list[OHLCVBar]:
        return self._store.query(
            as_of=self._as_of,
            start=start,
            end=end,
            instruments=[str(instrument)],
        )

    def all_bars(self) -> dict[InstrumentId, list[OHLCVBar]]:
        return self._store.all_as_of(self._as_of)
