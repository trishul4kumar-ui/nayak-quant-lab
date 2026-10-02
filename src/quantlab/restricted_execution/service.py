"""Fail-closed gateway for already-approved immutable broker-neutral intents."""
# ruff: noqa: E501

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.execution_authorization.models import AuthorizationScope, HumanApprovalRecord
from quantlab.execution_authorization.service import approval_valid
from quantlab.realtime_data.hashing import sha256
from quantlab.restricted_execution.adapter import (
    DisabledWriteAdapter,
    RestrictedWriteAdapter,
    SubmissionTimeout,
)
from quantlab.restricted_execution.models import (
    ExecutionEnvelope,
    ExecutionState,
    GatewayOrderIntent,
    GatewaySubmission,
    HumanConfirmation,
)
from quantlab.restricted_execution.repository import (
    confirmation,
    put_confirmation,
    put_envelope,
    put_submission,
    submission,
)
from quantlab.safety.kill_switch import is_active
from quantlab.safety.models import KillScope


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _hash(intent: GatewayOrderIntent, approval: HumanApprovalRecord) -> str:
    return sha256({"intent": intent.model_dump(mode="json"), "approval": approval.approval_hash})


class RestrictedExecutionGateway:
    """A narrow state machine, never a strategy, risk, sizing, or routing engine."""

    def __init__(self, adapter: RestrictedWriteAdapter | None = None) -> None:
        self._adapter = adapter or DisabledWriteAdapter()

    def draft(self, intent: GatewayOrderIntent, approval: HumanApprovalRecord) -> ExecutionEnvelope:
        now = _now()
        return put_envelope(
            ExecutionEnvelope(
                intent=intent,
                approval_id=approval.approval_id,
                assessment_hash=approval.assessment_hash,
                scope_hash=approval.scope_hash,
                envelope_hash=_hash(intent, approval),
                created_at=now,
            )
        )

    def validate(
        self,
        envelope: ExecutionEnvelope,
        approval: HumanApprovalRecord,
        scope: AuthorizationScope,
        *,
        now: datetime | None = None,
    ) -> ExecutionEnvelope:
        at = now or _now()
        errors: list[str] = []
        intent = envelope.intent
        if (
            envelope.approval_id != approval.approval_id
            or envelope.scope_hash != approval.scope_hash
        ):
            errors.append("approval or scope does not match immutable envelope")
        if not approval_valid(approval, scope, now=at):
            errors.append("approval is expired, revoked, or scope-mismatched")
        if intent.expires_at <= at:
            errors.append("order intent has expired")
        if not scope.session_start <= at <= scope.session_end:
            errors.append("outside approved session window")
        if intent.account_fingerprint != scope.broker_account_fingerprint:
            errors.append("account fingerprint is outside approved scope")
        if intent.security_id not in scope.allowed_security_ids:
            errors.append("security is outside approved scope")
        if intent.quantity <= 0 or intent.quantity != int(intent.quantity):
            errors.append("quantity must be a positive whole unit; no normalisation is allowed")
        if intent.order_type.lower() not in {"market", "limit"}:
            errors.append("unsupported order type")
        if intent.order_type.lower() == "limit" and (
            intent.limit_price is None or intent.limit_price <= 0
        ):
            errors.append("limit order requires unchanged positive limit price")
        if intent.action.value == "CANCEL" and not intent.broker_order_id:
            errors.append("cancellation requires an exact broker order identifier")
        action_scope = (
            KillScope.CANCEL_ORDER if intent.action.value == "CANCEL" else KillScope.NEW_ORDER
        )
        if is_active(KillScope.GLOBAL) or is_active(action_scope):
            errors.append("kill switch is active")
        state = ExecutionState.VALIDATED if not errors else ExecutionState.DRAFT
        return put_envelope(
            envelope.model_copy(update={"state": state, "validation_errors": tuple(errors)})
        )

    def confirm(
        self,
        envelope: ExecutionEnvelope,
        *,
        actor_id: str,
        confirmation_text: str,
        expires_at: datetime,
        now: datetime | None = None,
    ) -> ExecutionEnvelope:
        at = now or _now()
        if envelope.state is not ExecutionState.VALIDATED:
            raise ValueError("only a validated envelope may be human-confirmed")
        if not actor_id or actor_id.lower() in {"ai", "llm", "system"}:
            raise ValueError("AI and system actors cannot confirm submission")
        if expires_at <= at:
            raise ValueError("human confirmation has expired")
        expected = f"CONFIRM {envelope.envelope_hash}"
        if confirmation_text != expected:
            raise ValueError("exact envelope-hash confirmation is required")
        put_confirmation(
            HumanConfirmation(
                envelope_hash=envelope.envelope_hash,
                actor_id=actor_id,
                confirmation=confirmation_text,
                confirmed_at=at,
                expires_at=expires_at,
            )
        )
        return put_envelope(envelope.model_copy(update={"state": ExecutionState.CONFIRMED}))

    def submit(
        self, envelope: ExecutionEnvelope, *, interactive: bool = False, now: datetime | None = None
    ) -> GatewaySubmission:
        """Submit one time only. Timeout becomes SUBMISSION_UNKNOWN and is never retried."""
        at = now or _now()
        if not interactive:
            raise PermissionError("non-interactive submission is disabled")
        if envelope.state is not ExecutionState.CONFIRMED:
            raise ValueError("a current validated human confirmation is required")
        confirmed = confirmation(envelope.envelope_hash)
        if confirmed is None or confirmed.expires_at <= at:
            raise ValueError("human confirmation is missing or expired")
        existing = submission(envelope.envelope_hash)
        if existing is not None:
            raise ValueError("submission already attempted; reconcile instead of retrying")
        if not self._adapter.is_test_adapter:
            raise PermissionError("no production broker write adapter is enabled")
        put_envelope(envelope.model_copy(update={"state": ExecutionState.SUBMITTING}))
        correlation = f"restricted-{envelope.envelope_hash[:16]}"
        try:
            accepted, broker_order_id, detail = self._adapter.submit_once(envelope)
        except SubmissionTimeout as exc:
            result = put_submission(
                GatewaySubmission(
                    envelope_hash=envelope.envelope_hash,
                    state=ExecutionState.SUBMISSION_UNKNOWN,
                    attempted_at=at,
                    correlation_id=correlation,
                    detail=str(exc),
                    attempt_count=1,
                )
            )
            put_envelope(envelope.model_copy(update={"state": result.state}))
            return result
        state = ExecutionState.ACKNOWLEDGED if accepted else ExecutionState.REJECTED
        result = put_submission(
            GatewaySubmission(
                envelope_hash=envelope.envelope_hash,
                state=state,
                attempted_at=at,
                correlation_id=correlation,
                broker_order_id=broker_order_id,
                detail=detail,
                attempt_count=1,
            )
        )
        put_envelope(envelope.model_copy(update={"state": result.state}))
        return result

    def reconcile(
        self, envelope_hash: str, *, observed: bool, now: datetime | None = None
    ) -> GatewaySubmission:
        """Record read-only reconciliation of a previous attempt; never issue a retry."""
        current = submission(envelope_hash)
        if current is None:
            raise KeyError(envelope_hash)
        if current.state is not ExecutionState.SUBMISSION_UNKNOWN:
            return current
        result = put_submission(
            current.model_copy(
                update={
                    "state": ExecutionState.RECONCILED
                    if observed
                    else ExecutionState.SUBMISSION_UNKNOWN,
                    "reconciled_at": now or _now(),
                    "detail": "read-only reconciliation observed broker state"
                    if observed
                    else current.detail,
                }
            )
        )
        from quantlab.restricted_execution.repository import envelope as stored_envelope

        item = stored_envelope(envelope_hash)
        if item is not None:
            put_envelope(item.model_copy(update={"state": result.state}))
        return result
