from __future__ import annotations

import pytest

from quantlab.domain.research import CheckResult
from quantlab.release.integrity import report_from_result
from quantlab.release.models import ActorKind, CertificationRequest
from quantlab.release.service import evaluate

pytestmark = pytest.mark.release


def test_ai_override_fails_integrity() -> None:
    request = CertificationRequest(ai_override=True, actor=ActorKind.AI_SUGGESTION)
    result = evaluate(request)
    report = report_from_result(result, request)
    assert report.checks["ai_authorization_override"] is CheckResult.FAIL
    assert result.live_trading is False
