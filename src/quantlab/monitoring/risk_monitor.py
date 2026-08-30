"""Risk monitoring overlay. Does not mutate Prompt 05/08 limits."""

from __future__ import annotations

from quantlab.monitoring.concentration import herfindahl
from quantlab.monitoring.drawdown import drawdown_from_path
from quantlab.monitoring.models import EquityPoint, RiskObservation
from quantlab.monitoring.turnover import fill_turnover
from quantlab.paper_oms.models import PaperAccount, PaperFill


def risk_observation(
    account: PaperAccount,
    fills: list[PaperFill],
    path: list[EquityPoint],
) -> RiskObservation:
    base = drawdown_from_path(path)
    return base.model_copy(
        update={
            "concentration": herfindahl(account),
            "gross_exposure": account.gross_exposure,
            "net_exposure": account.net_exposure,
            "turnover": fill_turnover(fills, equity=account.equity),
        }
    )
