"""Selection must not migrate from the primary metric to whichever secondary looks strongest."""

from __future__ import annotations

from quantlab.orchestration.contracts import MetricRole, SelectionPolicy
from quantlab.orchestration.errors import OrchestrationError
from quantlab.orchestration.search_space import ResearchCandidate
from quantlab.orchestration.specification import ResearchSpec


class CandidateOutcome(ResearchCandidate):
    total_return: float | None = None
    sharpe: float | None = None
    max_drawdown: float | None = None
    p_value: float | None = None
    config_hash: str = ""
    ledger_id: str = ""
    selected: bool = False
    cached: bool = False


def select_primary(
    outcomes: list[CandidateOutcome],
    spec: ResearchSpec,
    *,
    policy: SelectionPolicy | None = None,
) -> CandidateOutcome | None:
    chosen = policy or spec.selection_policy
    if chosen is SelectionPolicy.MAX_SHARPE:
        raise OrchestrationError(
            "max-Sharpe selection after search is prohibited; use pre_registered"
        )
    primary = next(
        (m.name for m in spec.metrics if m.role is MetricRole.PRIMARY), spec.primary_metric
    )
    if primary != spec.primary_metric:
        raise OrchestrationError("primary metric migrated after freeze")
    for item in outcomes:
        if (
            item.lookback == spec.lookback
            and item.top_n == spec.top_n
            and abs(item.cost_bps - spec.cost_bps) < 1e-12
            and item.strategy_id == "cs_momentum_v1"
        ):
            item.selected = True
            return item
    if outcomes:
        outcomes[0].selected = True
        return outcomes[0]
    return None
