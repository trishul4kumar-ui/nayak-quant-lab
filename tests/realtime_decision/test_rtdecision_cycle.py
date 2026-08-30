from __future__ import annotations

import pytest

from quantlab.core.config import LiveSafetyGates
from quantlab.realtime_data.mock import SEED_AS_OF
from quantlab.realtime_decision.errors import DecisionBlocked, InvalidDecisionTransition
from quantlab.realtime_decision.models import (
    ActorKind,
    CertificationStatus,
    default_uncertified_release,
    synthetic_research_release,
)
from quantlab.realtime_decision.service import run_realtime_decision
from quantlab.realtime_decision.state import DecisionState, current, transition

pytestmark = pytest.mark.realtime_decision


def test_uncertified_release_abstains() -> None:
    item = run_realtime_decision(release=default_uncertified_release(as_of=SEED_AS_OF))
    assert item.target is None
    assert item.live_trading is False
    assert item.state == DecisionState.ABSTAINED.value
    assert LiveSafetyGates().live_trading is False


def test_research_release_decides_without_order() -> None:
    item = run_realtime_decision(release=synthetic_research_release(as_of=SEED_AS_OF))
    assert item.target is not None
    assert item.state == DecisionState.DECIDED.value
    assert "order" in item.note.lower() or item.live_trading is False
    assert item.target.note
    assert LiveSafetyGates().broker_write_enabled is False


def test_expired_release_blocks() -> None:
    release = synthetic_research_release(as_of=SEED_AS_OF).model_copy(
        update={"certification_status": CertificationStatus.EXPIRED}
    )
    item = run_realtime_decision(release=release)
    assert item.target is None
    assert item.state == DecisionState.BLOCKED.value


def test_ai_actor_blocked() -> None:
    with pytest.raises(DecisionBlocked):
        run_realtime_decision(
            release=synthetic_research_release(as_of=SEED_AS_OF),
            actor=ActorKind.AI_SUGGESTION,
        )


def test_decision_hash_stable() -> None:
    first = run_realtime_decision(release=synthetic_research_release(as_of=SEED_AS_OF))
    second = run_realtime_decision(release=synthetic_research_release(as_of=SEED_AS_OF))
    assert first.decision_hash == second.decision_hash


def test_illegal_decision_transition() -> None:
    assert current() is DecisionState.OBSERVING
    with pytest.raises(InvalidDecisionTransition):
        transition(DecisionState.DECIDED)
