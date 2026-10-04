from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from quantlab.broker_gateway.service import reset_for_tests as reset_broker
from quantlab.execution_authorization.models import (
    AuthorizationAssessment,
    AuthorizationPolicy,
    AuthorizationScope,
    AuthorizationState,
)
from quantlab.execution_authorization.repository import reset_for_tests
from quantlab.execution_authorization.service import approval_valid, approve, assess, revoke
from quantlab.production_shadow.repository import reset_for_tests as reset_shadow
from quantlab.realtime_data.hashing import sha256
from quantlab.reconciliation.repository import reset_for_tests as reset_reconciliation
from quantlab.release.service import reset_for_tests as reset_release
from quantlab.safety.kill_switch import activate
from quantlab.safety.models import KillScope
from quantlab.safety.service import reset_for_tests as reset_safety


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_for_tests()
    # These are process-global upstream stores. A preceding shadow test may leave
    # failed evidence behind; that is not the missing-evidence scenario below.
    reset_broker()
    reset_shadow()
    reset_reconciliation()
    reset_release()
    reset_safety()


def _scope() -> AuthorizationScope:
    now = datetime.now(tz=UTC)
    return AuthorizationScope(
        deployment_id="test",
        broker_account_fingerprint="account-hash",
        allowed_security_ids=("NSE:TCS",),
        universe_version="test-v1",
        strategy_hash="strategy",
        model_hash="model",
        portfolio_policy_hash="portfolio",
        release_id="release",
        data_provider="fixture",
        data_policy_hash="data-policy",
        risk_policy_hash="risk-policy",
        max_gross_exposure=1.0,
        max_notional=100.0,
        max_turnover=0.1,
        operating_mode="restricted_live_review",
        session_start=now,
        session_end=now + timedelta(minutes=5),
        expiry=now + timedelta(minutes=10),
    )


def _eligible(scope: AuthorizationScope) -> AuthorizationAssessment:
    digest = sha256({"scope": scope.model_dump(mode="json"), "fixture": "eligible"})
    return AuthorizationAssessment(
        assessment_id="assessment-fixture",
        scope=scope,
        policy=AuthorizationPolicy(require_shadow_replay=False),
        checks=(),
        blockers=(),
        evidence_hashes=(),
        state=AuthorizationState.ELIGIBLE_FOR_HUMAN_REVIEW,
        assessed_at=datetime.now(tz=UTC),
        assessment_hash=digest,
    )


def test_default_assessment_is_blocked_when_critical_evidence_is_missing() -> None:
    result = assess(_scope())
    assert result.state is AuthorizationState.INELIGIBLE
    assert "release_certification" in result.blockers
    assert result.live_trading is False
    assert result.broker_write_enabled is False


def test_failed_safety_evidence_is_blocked_not_merely_ineligible() -> None:
    activate(KillScope.GLOBAL, reason="test incident")
    result = assess(_scope())
    assert result.state is AuthorizationState.BLOCKED
    assert "kill_switch" in result.blockers
    assert result.live_trading is False
    assert result.broker_write_enabled is False


def test_ai_cannot_approve_and_human_approval_is_exact_hash_bound() -> None:
    scope = _scope()
    assessment = _eligible(scope)
    confirmation = f"APPROVE {assessment.assessment_hash}"
    with pytest.raises(ValueError, match="AI"):
        approve(assessment, approver_id="ai", confirmation=confirmation)
    approval = approve(assessment, approver_id="human-1", confirmation=confirmation)
    assert approval_valid(approval, scope)
    changed = scope.model_copy(update={"max_notional": 101.0})
    assert approval_valid(approval, changed) is False
    assert revoke(approval.approval_id, reason="scope changed", revoked_by="human-1")
    assert approval_valid(approval, scope) is False


def test_execution_authorization_has_no_broker_write_path() -> None:
    source = "\n".join(
        item.read_text() for item in Path("src/quantlab/execution_authorization").glob("*.py")
    )
    for forbidden in ("place_order", "cancel_order", "modify_order"):
        assert forbidden not in source
