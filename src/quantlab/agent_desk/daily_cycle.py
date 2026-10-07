"""Finite daily state reducer. No background loops or provider invocations."""

from quantlab.agent_desk.models import DeskPhase, DeskSession


def phase_for_session(session: DeskSession, *, paused: bool = False) -> DeskPhase:
    if paused:
        return DeskPhase.PAUSED
    return {
        DeskSession.CLOSED: DeskPhase.OFF,
        DeskSession.PRE_MARKET: DeskPhase.PRE_MARKET,
        DeskSession.OPENING: DeskPhase.OPENING_OBSERVATION,
        DeskSession.CONTINUOUS: DeskPhase.INTRADAY_RESEARCH,
        DeskSession.CLOSING: DeskPhase.CLOSING_REVIEW,
        DeskSession.POST_MARKET: DeskPhase.POST_MARKET_RESEARCH,
    }[session]


def next_research_phase(phase: DeskPhase) -> DeskPhase:
    """Explicit post-market transitions; interrupt states cannot advance automatically."""
    return {
        DeskPhase.POST_MARKET_RESEARCH: DeskPhase.DAILY_RECONCILIATION,
        DeskPhase.DAILY_RECONCILIATION: DeskPhase.LEARNING_REVIEW,
        DeskPhase.LEARNING_REVIEW: DeskPhase.COMPLETE,
    }.get(phase, phase)
