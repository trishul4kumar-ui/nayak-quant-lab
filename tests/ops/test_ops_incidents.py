from __future__ import annotations

from quantlab.ops.incidents import list_incidents, record


def test_incidents_are_retained() -> None:
    record(kind="process_crash", detail="app failed")
    assert list_incidents()[-1].kind == "process_crash"
