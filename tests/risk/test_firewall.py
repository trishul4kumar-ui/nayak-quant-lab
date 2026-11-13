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


def test_name_count_limit_rejects_without_a_modified_portfolio() -> None:
    instruments = [
        Instrument(id=InstrumentId.parse("NSE:TCS")),
        Instrument(id=InstrumentId.parse("NSE:INFY")),
    ]
    fw = RiskFirewall(RiskLimits(max_names=1))
    fw.register_instruments(instruments)
    proposal = ProposedPortfolio(
        as_of=datetime.now(tz=UTC),
        targets=[TargetPosition(instrument=inst.id, weight=0.1) for inst in instruments],
    )
    decision = fw.authorize(proposal)
    assert decision.verdict is RiskVerdict.REJECT
    assert decision.reasons == ["too_many_names"]
    assert decision.modified is None
    with pytest.raises(RiskRejectedError):
        fw.require(proposal)


def test_duplicate_instrument_cannot_bypass_name_limit() -> None:
    inst = Instrument(id=InstrumentId.parse("NSE:TCS"))
    fw = RiskFirewall(RiskLimits(max_name_weight=0.4))
    fw.register_instruments([inst])
    proposal = ProposedPortfolio(
        as_of=datetime.now(tz=UTC),
        targets=[TargetPosition(instrument=inst.id, weight=0.3) for _ in range(2)],
    )
    decision = fw.authorize(proposal)
    assert decision.verdict is RiskVerdict.REJECT
    assert "duplicate_instrument" in decision.reasons


@pytest.mark.parametrize("weight", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_weights_fail_closed(weight: float) -> None:
    inst = Instrument(id=InstrumentId.parse("NSE:TCS"))
    fw = RiskFirewall()
    fw.register_instruments([inst])
    decision = fw.authorize(ProposedPortfolio(
        as_of=datetime.now(tz=UTC), targets=[TargetPosition(instrument=inst.id, weight=weight)]
    ))
    assert decision.verdict is RiskVerdict.REJECT
    assert "nonfinite_weight" in decision.reasons


def test_allowed_short_is_clipped_by_absolute_name_limit() -> None:
    inst = Instrument(id=InstrumentId.parse("NSE:TCS"))
    fw = RiskFirewall(RiskLimits(max_name_weight=0.4, allow_short=True))
    fw.register_instruments([inst])
    decision = fw.authorize(ProposedPortfolio(
        as_of=datetime.now(tz=UTC), targets=[TargetPosition(instrument=inst.id, weight=-0.8)]
    ))
    assert decision.verdict is RiskVerdict.MODIFY
    assert decision.modified is not None
    assert decision.modified.targets[0].weight == pytest.approx(-0.4)


@pytest.mark.parametrize(
    "limits", [dict(max_name_weight=float("nan")), dict(max_name_weight=True),
               dict(max_gross=float("inf")), dict(max_gross=True),
               dict(max_names=-1), dict(max_names=True)]
)
def test_invalid_limit_configuration_is_rejected(limits: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        RiskLimits(**limits)  # type: ignore[arg-type]


def test_mutated_invalid_limits_fail_closed() -> None:
    inst = Instrument(id=InstrumentId.parse("NSE:TCS"))
    limits = RiskLimits()
    fw = RiskFirewall(limits)
    fw.register_instruments([inst])
    limits.max_gross = float("nan")
    decision = fw.authorize(ProposedPortfolio(
        as_of=datetime.now(tz=UTC), targets=[TargetPosition(instrument=inst.id, weight=0.2)]
    ))
    assert decision.verdict is RiskVerdict.REJECT
    assert decision.reasons == ["invalid_risk_limits"]


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
