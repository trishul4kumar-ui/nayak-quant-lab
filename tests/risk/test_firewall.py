from datetime import UTC, datetime

import pytest

from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import RiskRejectedError, SafetyError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import Instrument, ProposedPortfolio, RiskVerdict, TargetPosition
from quantlab.execution.engine import ExecutionEngine
from quantlab.risk.firewall import RiskFirewall, RiskLimits


def test_firewall_rejects_unlisted() -> None:
    fw = RiskFirewall()
    fw.register_instruments([Instrument(id=InstrumentId.parse("NSE:TCS"))])
    proposal = ProposedPortfolio(
        as_of=datetime.now(tz=UTC),
        targets=[TargetPosition(instrument=InstrumentId.parse("NSE:FOO"), weight=1.0)],
    )
    decision = fw.authorize(proposal)
    assert decision.verdict is RiskVerdict.REJECT


def test_firewall_unhealthy_fails_closed() -> None:
    fw = RiskFirewall(healthy=False)
    fw.register_instruments([Instrument(id=InstrumentId.parse("NSE:TCS"))])
    proposal = ProposedPortfolio(
        as_of=datetime.now(tz=UTC),
        targets=[TargetPosition(instrument=InstrumentId.parse("NSE:TCS"), weight=0.2)],
    )
    with pytest.raises(RiskRejectedError):
        fw.require(proposal)


def test_limits_clip_name_weight() -> None:
    fw = RiskFirewall(RiskLimits(max_name_weight=0.4, max_gross=1.0))
    inst = Instrument(id=InstrumentId.parse("NSE:TCS"))
    fw.register_instruments([inst])
    proposal = ProposedPortfolio(
        as_of=datetime.now(tz=UTC),
        targets=[TargetPosition(instrument=inst.id, weight=1.0)],
    )
    decision = fw.authorize(proposal)
    assert decision.verdict is RiskVerdict.MODIFY
    assert decision.modified is not None
    assert decision.modified.targets[0].weight == pytest.approx(0.4)


def test_live_submit_blocked() -> None:
    engine = ExecutionEngine(LiveSafetyGates())
    from quantlab.domain.models import Order, Side

    order = Order(
        id="x",
        instrument=InstrumentId.parse("NSE:TCS"),
        side=Side.BUY,
        quantity=1,
    )
    with pytest.raises(SafetyError):
        engine.submit(order, live=True)
