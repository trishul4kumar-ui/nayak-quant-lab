import pytest

from quantlab.brokers.paper import OpenAlgoGateway, PaperGateway
from quantlab.core.errors import SafetyError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import Order, Side


def test_paper_gateway_records_orders() -> None:
    gw = PaperGateway()
    order = Order(
        id="p1",
        instrument=InstrumentId.parse("NSE:INFY"),
        side=Side.BUY,
        quantity=10,
    )
    placed = gw.place_order(order)
    assert placed.status.value == "acknowledged"
    assert len(gw.get_orders()) == 1


def test_openalgo_disabled() -> None:
    gw = OpenAlgoGateway()
    order = Order(
        id="x",
        instrument=InstrumentId.parse("NSE:INFY"),
        side=Side.BUY,
        quantity=1,
    )
    with pytest.raises(SafetyError):
        gw.place_order(order)
