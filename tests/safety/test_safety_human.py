from __future__ import annotations

from datetime import UTC, datetime

from quantlab.safety.human_authorization import record
from quantlab.safety.kill_switch import KillScope
from quantlab.safety.models import ActorKind, HumanApproval, SafetyRequest
from quantlab.safety.service import evaluate_request, kill


def test_human_authorization_cannot_bypass_safety_gates() -> None:
    record(
        HumanApproval(
            approval_id="human-1",
            actor=ActorKind.HUMAN,
            reason="arm",
            timestamp=datetime(2024, 1, 2, tzinfo=UTC),
        )
    )
    kill(KillScope.GLOBAL, reason="still blocked")
    result = evaluate_request(SafetyRequest(human_approval_id="human-1", live_release=False))
    assert result.gate("G10_KILL_SWITCH").blocks_release
    assert result.gate("G15_FINAL_RELEASE").blocks_release
    assert result.live_release_authorized is False
