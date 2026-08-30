from datetime import UTC, datetime

import pytest

from quantlab.core.errors import RiskRejectedError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import Instrument, ProposedPortfolio, TargetPosition
from quantlab.risk.firewall import RiskFirewall
from quantlab.risk.states import RiskState


def test_halt_rejects_all_new_exposure() -> None:
    fw = RiskFirewall(state=RiskState.HALT)
    inst = Instrument(id=InstrumentId.parse("NSE:TCS"))
    fw.register_instruments([inst])
    proposal = ProposedPortfolio(
        as_of=datetime.now(tz=UTC),
        targets=[TargetPosition(instrument=inst.id, weight=0.1)],
    )
    with pytest.raises(RiskRejectedError, match="risk_state"):
        fw.require(proposal)
