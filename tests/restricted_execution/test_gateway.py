from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quantlab.execution_authorization.models import AuthorizationScope, HumanApprovalRecord
from quantlab.realtime_data.hashing import sha256
from quantlab.restricted_execution.adapter import MockRestrictedWriteAdapter
from quantlab.restricted_execution.models import ExecutionState, GatewayOrderIntent
from quantlab.restricted_execution.repository import reset_for_tests
from quantlab.restricted_execution.service import RestrictedExecutionGateway


def _scope(now: datetime) -> AuthorizationScope:
    return AuthorizationScope(
        deployment_id="deploy",
        broker_account_fingerprint="acct-hash",
        allowed_security_ids=("NSE:ABC",),
        universe_version="u1",
        strategy_hash="strategy",
        model_hash="model",
        portfolio_policy_hash="portfolio",
        release_id="release",
        data_provider="test",
        data_policy_hash="data",
        risk_policy_hash="risk",
        max_gross_exposure=1.0,
        max_notional=1000.0,
        max_turnover=1.0,
        operating_mode="restricted",
        session_start=now - timedelta(minutes=1),
        session_end=now + timedelta(minutes=5),
        expiry=now + timedelta(minutes=5),
    )


def _approval(scope: AuthorizationScope, now: datetime) -> HumanApprovalRecord:
    return HumanApprovalRecord(
        approval_id="approval-1",
        assessment_id="assessment-1",
        assessment_hash="assessment-hash",
        scope_hash=sha256(scope.model_dump(mode="json")),
        approver_id="vaibhav",
        approved_at=now,
        expires_at=scope.expiry,
        confirmation="APPROVE assessment-hash",
        approval_hash="approval-hash",
    )


def _intent(now: datetime) -> GatewayOrderIntent:
    return GatewayOrderIntent(
        request_id="request-1",
        account_fingerprint="acct-hash",
        security_id="NSE:ABC",
        side="BUY",
        quantity=1,
        order_type="limit",
        limit_price=100.0,
        created_at=now,
        expires_at=now + timedelta(minutes=3),
        idempotency_key="idem-1",
    )


def test_timeout_is_unknown_and_never_retried() -> None:
    reset_for_tests()
    now = datetime(2026, 1, 2, tzinfo=UTC)
    scope = _scope(now)
    approval = _approval(scope, now)
    adapter = MockRestrictedWriteAdapter(outcome="timeout")
    gateway = RestrictedExecutionGateway(adapter)
    drafted = gateway.draft(_intent(now), approval)
    valid = gateway.validate(drafted, approval, scope, now=now)
    confirmed = gateway.confirm(
        valid,
        actor_id="vaibhav",
        confirmation_text=f"CONFIRM {valid.envelope_hash}",
        expires_at=now + timedelta(minutes=2),
        now=now,
    )
    result = gateway.submit(confirmed, interactive=True, now=now)

    assert result.state is ExecutionState.SUBMISSION_UNKNOWN
    assert len(adapter.calls) == 1
    with pytest.raises(ValueError, match="reconcile instead of retrying"):
        gateway.submit(confirmed, interactive=True, now=now)


def test_noninteractive_submission_is_blocked() -> None:
    reset_for_tests()
    now = datetime(2026, 1, 2, tzinfo=UTC)
    scope = _scope(now)
    approval = _approval(scope, now)
    gateway = RestrictedExecutionGateway(MockRestrictedWriteAdapter())
    valid = gateway.validate(gateway.draft(_intent(now), approval), approval, scope, now=now)
    confirmed = gateway.confirm(
        valid,
        actor_id="vaibhav",
        confirmation_text=f"CONFIRM {valid.envelope_hash}",
        expires_at=now + timedelta(minutes=2),
        now=now,
    )
    with pytest.raises(PermissionError, match="non-interactive"):
        gateway.submit(confirmed, interactive=False, now=now)
