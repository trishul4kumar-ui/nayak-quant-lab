from __future__ import annotations

from quantlab.ops.audit import mark_failure, writer_healthy
from quantlab.ops.readiness import ready
from quantlab.ops.service import doctor
from quantlab.ops.state import OpsState, force


def test_audit_failure_affects_readiness() -> None:
    doctor()
    mark_failure()
    assert writer_healthy() is False
    force(OpsState.RUNNING)
    assert ready() is False
