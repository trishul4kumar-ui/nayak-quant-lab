from __future__ import annotations

from quantlab.ops.models import ProcessStatus
from quantlab.ops.supervisor import fail, processes, restart_one


def test_process_crash_is_detected() -> None:
    item = fail("app", error="boom")
    assert item.status is ProcessStatus.FAILED
    assert processes()["app"].status is ProcessStatus.FAILED


def test_crash_loop_is_contained() -> None:
    fail("scheduler", error="boom")
    last = restart_one("scheduler")
    for _ in range(8):
        fail("scheduler", error="boom")
        last = restart_one("scheduler")
    assert last.status is ProcessStatus.CRASH_LOOP
    assert last.restarts > last.max_restarts
