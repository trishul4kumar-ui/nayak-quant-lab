"""Approved PIT market-data contract. Strategies never see unrestricted tables."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.errors import LookAheadError
from quantlab.core.time import as_utc
from quantlab.data.fabric.layout import FabricLayout, resolve_fabric_root
from quantlab.data.fabric.store import PitStore
from quantlab.domain.models import OHLCVBar


def get(
    *,
    security_id: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    as_of: datetime,
    dataset_id: str = "",
    version: str = "",
    layout: FabricLayout | None = None,
    bars: list[OHLCVBar] | None = None,
) -> list[OHLCVBar]:
    """Return observations with available_time <= as_of. Never invents prices."""
    cutoff = as_utc(as_of)
    if bars is not None:
        out = [
            bar
            for bar in bars
            if bar.pit.available_time <= cutoff
            and (
                security_id is None
                or str(bar.instrument) == security_id
                or bar.instrument.symbol == security_id
            )
            and (start is None or bar.pit.event_time >= as_utc(start))
            and (end is None or bar.pit.event_time <= as_utc(end))
        ]
        for bar in out:
            if bar.pit.available_time > cutoff:
                raise LookAheadError("future_available_data")
        return out
    if not dataset_id or not version:
        return []
    store = PitStore(layout or FabricLayout(resolve_fabric_root()), dataset_id, version)
    instruments = None if security_id is None else [security_id]
    return store.query(as_of=cutoff, start=start, end=end, instruments=instruments)
