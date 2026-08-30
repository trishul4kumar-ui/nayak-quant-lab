"""Replay adapter. Frozen observations only. Not a live feed."""

from __future__ import annotations

from quantlab.realtime_data.models import MarketObservation


class ReplayMarketDataAdapter:
    source_id = "replay-observe-only"
    write_enabled = False

    def __init__(self, observations: tuple[MarketObservation, ...]) -> None:
        self._observations = observations
        self._connected = False
        self._emitted = False

    def connect(self) -> None:
        self._connected = True
        self._emitted = False

    def disconnect(self) -> None:
        self._connected = False

    def poll(self) -> tuple[MarketObservation, ...]:
        if not self._connected or self._emitted:
            return ()
        self._emitted = True
        return self._observations
