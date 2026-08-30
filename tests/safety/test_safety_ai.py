from __future__ import annotations

import pytest

from quantlab.safety.errors import ReleaseBlocked
from quantlab.safety.models import ActorKind, SafetyRequest
from quantlab.safety.service import authorize, evaluate_request


def test_ai_cannot_override() -> None:
    result = evaluate_request(SafetyRequest(ai_override=True))
    assert result.gate("G13_AI_BOUNDARY").blocks_release
    assert any(item.kind == "ai_safety_override" for item in result.incidents)


def test_ai_cannot_authorize() -> None:
    with pytest.raises(ReleaseBlocked):
        authorize(SafetyRequest(actor=ActorKind.AI_SUGGESTION, live_release=False))
