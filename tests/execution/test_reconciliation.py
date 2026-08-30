import pytest

from quantlab.core.errors import SafetyError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import PortfolioState, Position
from quantlab.execution.reconciliation import ReconciliationEngine


def test_position_mismatch_blocks_live() -> None:
    engine = ReconciliationEngine()
    internal = PortfolioState(
        cash=1.0,
        positions=[Position(instrument=InstrumentId.parse("NSE:TCS"), quantity=1)],
    )
    report = engine.compare(internal, broker_cash=1.0, broker_positions=[], open_orders=[])
    assert report.matched is False
    with pytest.raises(SafetyError):
        engine.require_live_clearance(report)


def test_matched_state_allows_live_flag() -> None:
    engine = ReconciliationEngine()
    pos = Position(instrument=InstrumentId.parse("NSE:TCS"), quantity=2)
    internal = PortfolioState(cash=100.0, positions=[pos])
    report = engine.compare(internal, 100.0, [pos], [])
    assert report.allows_live_orders() is True
