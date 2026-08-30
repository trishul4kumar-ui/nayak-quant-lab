from __future__ import annotations

from quantlab.ops.supervisor import mark_cycle


def test_restart_does_not_duplicate_paper_shadow_runs() -> None:
    assert mark_cycle("cycle-1") is True
    assert mark_cycle("cycle-1") is False
