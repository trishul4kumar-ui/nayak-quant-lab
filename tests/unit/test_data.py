from datetime import UTC, datetime, timedelta

import pytest

from quantlab.core.errors import DataIntegrityError
from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.data.validation import validate_bars
from quantlab.domain.models import OHLCVBar


def test_memory_provider_valid_series() -> None:
    provider = MemoryBarProvider(n_days=30)
    for inst in provider.get_instruments():
        validate_bars(provider.all_bars()[inst.id])


def test_non_monotonic_bars_fail() -> None:
    day = datetime(2024, 1, 2, tzinfo=UTC)
    pit = PointInTime(event_time=day, effective_time=day, available_time=day, ingestion_time=day)
    later = PointInTime(
        event_time=day + timedelta(days=1),
        effective_time=day + timedelta(days=1),
        available_time=day + timedelta(days=1),
        ingestion_time=day + timedelta(days=1),
    )
    inst = InstrumentId(exchange="NSE", symbol="TCS")
    a = OHLCVBar(instrument=inst, pit=later, open=10, high=11, low=9, close=10)
    b = OHLCVBar(instrument=inst, pit=pit, open=10, high=11, low=9, close=10)
    with pytest.raises(DataIntegrityError):
        validate_bars([a, b])
