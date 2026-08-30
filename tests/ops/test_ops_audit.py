from __future__ import annotations

from quantlab.ops.audit import flushed, history
from quantlab.ops.service import doctor, shutdown


def test_shutdown_flushes_audit_state() -> None:
    doctor()
    assert history()
    count = shutdown()
    assert count >= 1
    assert flushed() is True
