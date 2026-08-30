"""Market-data adapter protocol. No vendor SDKs. Observe-only."""

from __future__ import annotations

from typing import Protocol

from quantlab.realtime_data.models import MarketObservation


class MarketDataAdapter(Protocol):
    source_id: str
    write_enabled: bool

    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def poll(self) -> tuple[MarketObservation, ...]: ...
