"""Write boundary protocol. The only bundled adapter is a test double."""

from __future__ import annotations

from typing import Protocol

from quantlab.restricted_execution.models import ExecutionEnvelope


class SubmissionTimeout(TimeoutError):
    """An ambiguous result; callers must reconcile and may not retry."""


class RestrictedWriteAdapter(Protocol):
    is_test_adapter: bool

    def submit_once(self, envelope: ExecutionEnvelope) -> tuple[bool, str, str]: ...


class DisabledWriteAdapter:
    """Production default: no executable broker adapter is present."""

    is_test_adapter = False

    def submit_once(self, envelope: ExecutionEnvelope) -> tuple[bool, str, str]:
        del envelope
        raise PermissionError("no production broker write adapter is enabled")


class MockRestrictedWriteAdapter:
    """Test-only deterministic adapter. It has no network or broker dependency."""

    is_test_adapter = True

    def __init__(self, outcome: str = "acknowledged") -> None:
        self.outcome = outcome
        self.calls: list[str] = []

    def submit_once(self, envelope: ExecutionEnvelope) -> tuple[bool, str, str]:
        self.calls.append(envelope.envelope_hash)
        if self.outcome == "timeout":
            raise SubmissionTimeout("simulated ambiguous timeout")
        if self.outcome == "rejected":
            return False, "", "simulated rejection"
        return True, f"mock-{envelope.intent.request_id}", "simulated acknowledgement"
