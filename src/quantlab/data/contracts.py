from datetime import datetime
from typing import Protocol, runtime_checkable

from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import Instrument, OHLCVBar


@runtime_checkable
class MarketDataProvider(Protocol):
    """Vendor-neutral market data. Research never imports a broker SDK."""

    def get_instruments(self) -> list[Instrument]: ...

    def get_bars(
        self,
        instrument: InstrumentId,
        start: datetime,
        end: datetime,
    ) -> list[OHLCVBar]: ...
