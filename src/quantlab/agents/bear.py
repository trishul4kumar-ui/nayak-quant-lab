"""Independent downside research; exposure intent never establishes eligibility."""

from __future__ import annotations

from datetime import datetime

from quantlab.agents.analyst_worker import AnalystWorker, bull_mandate
from quantlab.agents.context import FrozenHistory, create_context
from quantlab.agents.contracts import (
    AgentMandate,
    AgentRole,
    AgentRunContext,
    AgentVersion,
    ResearchMode,
)
from quantlab.agents.errors import AgentContextError
from quantlab.agents.hashing import digest
from quantlab.agents.prompts import SYSTEM_SAFETY_POLICY
from quantlab.agents.provider import AgentModelProvider
from quantlab.agents.repository import AgentRepository
from quantlab.agents.research import AnalystMemoDraft, BearMemoDraft, BearResearchMemo, ResearchPlan
from quantlab.realtime_data.models import RealTimeSnapshot

BEAR_MANDATE = (
    "Independently investigate downside hypotheses, not the negation of Bull's score. "
    "Study negative momentum, breakdowns, failed breakouts, mean reversion against longs, "
    "volatility expansion, tail/drawdown risk, factor crowding, correlation spikes, liquidity "
    "and adverse regimes. Examine squeeze/reversal risks and evidence against your own thesis. "
    "AVOID, REDUCE, HEDGE, EXIT, MORE_RESEARCH and NO_TRADE are valid alternatives to SHORT. "
    "Separate economic downside rationale from a legally/operationally eligible instrument. "
    "Eligibility is UNKNOWN until a deterministic downstream check; never assume an overnight "
    "cash-equity short is available. No position is verified here, and no sizing or order prices. "
    "Missing costs, OOS/walk-forward or validation are NOT_TESTED, not PASS."
)


def bear_mandate(now: datetime) -> AgentMandate:
    return AgentMandate(
        created_at=now, role=AgentRole.BEAR, mandate=BEAR_MANDATE, granted=bull_mandate(now).granted
    )


def create_bear_context(
    repository: AgentRepository,
    snapshot: RealTimeSnapshot,
    provider: AgentModelProvider,
    *,
    now: datetime,
    history: FrozenHistory | None = None,
    mode: ResearchMode = ResearchMode.RESEARCH,
) -> AgentRunContext:
    if len({row.security_id for row in snapshot.observations}) > 20:
        raise AgentContextError("RESEARCH_SCOPE_BUDGET_EXCEEDED")
    if history is not None and len(history.bars_json) > 5040:
        raise AgentContextError("HISTORY_BUDGET_EXCEEDED")
    mandate = bear_mandate(now)
    version = AgentVersion(
        created_at=now,
        version="41.1",
        implementation_version="41-v1",
        prompt_hash=digest(
            {
                "system": SYSTEM_SAFETY_POLICY,
                "mandate": mandate.mandate,
                "plan": ResearchPlan.model_json_schema(),
                "memo": BearMemoDraft.model_json_schema(),
            }
        ),
    )
    return create_context(
        repository,
        snapshot,
        mandate=mandate,
        model=provider.identity(),
        now=now,
        mode=mode,
        history=history,
        agent_version=version,
    )


def search_bear_history(
    repository: AgentRepository, query: str = "", *, as_of: datetime | None = None
) -> tuple[BearResearchMemo, ...]:
    needle = query.strip().casefold()
    return tuple(
        memo
        for memo in repository.list(BearResearchMemo)
        if (as_of is None or memo.created_at <= as_of)
        and (not needle or needle in memo.model_dump_json().casefold())
    )


class BearWorker(AnalystWorker):
    role = AgentRole.BEAR
    implementation_version = "41-v1"
    direction = "independent downside / risk"
    draft_contract = BearMemoDraft
    memo_contract = BearResearchMemo
    mandate_factory = staticmethod(bear_mandate)
    ascending_screen = True
    extra_task = BEAR_MANDATE

    def extra_memo_fields(self, draft: AnalystMemoDraft, now: datetime) -> dict[str, object]:
        if not isinstance(draft, BearMemoDraft):
            raise AgentContextError("BEAR_DRAFT_REQUIRED")
        return {
            "exposure_archetype": draft.exposure,
            "instrument_eligibility": "UNKNOWN",
            "squeeze_reversal_risks": draft.squeeze_reversal_risks,
            "liquidity_risks": draft.liquidity_risks,
        }

    def exposure_intent(self, draft: AnalystMemoDraft) -> str:
        if not isinstance(draft, BearMemoDraft):
            raise AgentContextError("BEAR_DRAFT_REQUIRED")
        return f"{draft.exposure}: research intent only; eligibility UNKNOWN"

    def extra_evidence(self) -> dict[str, object]:
        return {"instrument_eligibility": "UNKNOWN", "existing_position": "NOT_TESTED"}

    def host_uncertainties(self) -> tuple[str, ...]:
        return (
            "Instrument eligibility UNKNOWN; no overnight cash-equity short is assumed.",
            "Existing positions NOT_TESTED; REDUCE/EXIT/HEDGE are research opinions only.",
        )
