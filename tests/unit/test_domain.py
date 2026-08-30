from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.domain.models import Instrument, OHLCVBar, Order, OrderStatus, Side


def test_instrument_id_normalizes() -> None:
    ident = InstrumentId(exchange="nse", symbol="reliance")
    assert str(ident) == "NSE:RELIANCE"


def test_bar_rejects_broken_ohlc() -> None:
    day = datetime(2024, 1, 2, tzinfo=UTC)
    pit = PointInTime(event_time=day, effective_time=day, available_time=day, ingestion_time=day)
    with pytest.raises(ValidationError):
        OHLCVBar(
            instrument=InstrumentId(exchange="NSE", symbol="TCS"),
            pit=pit,
            open=10,
            high=9,
            low=8,
            close=9.5,
        )


def test_order_states_include_reconciling() -> None:
    assert OrderStatus.RECONCILING.value == "reconciling"
    assert OrderStatus.RISK_PENDING.value == "risk_pending"
    order = Order(
        id="1",
        instrument=InstrumentId(exchange="NSE", symbol="INFY"),
        side=Side.BUY,
        quantity=1,
    )
    assert order.status is OrderStatus.CREATED


def test_instrument_lot_size() -> None:
    inst = Instrument(id=InstrumentId.parse("NSE:HDFCBANK"), lot_size=1)
    assert inst.listed is True
