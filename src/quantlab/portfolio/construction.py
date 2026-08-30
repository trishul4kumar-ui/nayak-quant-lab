from datetime import datetime

from quantlab.domain.models import ProposedPortfolio, Signal, TargetPosition
from quantlab.research.strategy import Strategy


def construct_portfolio(
    strategy: Strategy,
    signals: list[Signal],
    as_of: datetime,
    reason: str,
) -> ProposedPortfolio:
    """Signal → target weights. Not an order."""
    targets: list[TargetPosition] = strategy.target_positions(signals)
    return ProposedPortfolio(as_of=as_of, targets=targets, reason=reason)
