from __future__ import annotations

import time
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from quantlab.app.assistant import FocusAction, NayakAssistant
from quantlab.app.bootstrap import bootstrap
from quantlab.app.copy import SYNTHETIC_SHARPE_DISCLAIMER
from quantlab.app.jobs import JobStatus


def _wait_for_job(runtime, job_id: str, *, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = runtime.jobs.get(job_id)
        if job is not None and job.status in {JobStatus.COMPLETED, JobStatus.FAILED}:
            return
        time.sleep(0.05)
    raise TimeoutError(f"job {job_id} did not finish")


def _run_backtest(runtime) -> None:
    job = runtime.submit_momentum_backtest(
        {"n_days": 60, "lookback": 20, "top_n": 2, "cost_bps": 10.0}
    )
    _wait_for_job(runtime, job.job_id)


@pytest.mark.desktop
def test_journal_groups_deduplicate_names(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    assistant = NayakAssistant(runtime)
    assistant.complete_onboarding()
    for _ in range(3):
        _run_backtest(runtime)
    groups = assistant.journal_groups(limit=5)
    assert groups
    assert any(group.count >= 2 for group in groups)


@pytest.mark.desktop
def test_primary_context_nudge_single_message(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    assistant = NayakAssistant(runtime)
    assistant.complete_onboarding()
    nudge = assistant.primary_context_nudge()
    assert nudge is not None
    assert len(nudge.text) > 10
    assert len(assistant.context_nudges()) == 1


@pytest.mark.desktop
def test_focus_suggests_journal_after_validation(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    assistant = NayakAssistant(runtime)
    assistant.complete_onboarding()
    _run_backtest(runtime)
    assistant.record_milestone("first_backtest")
    assistant.record_milestone("first_equity_view")
    val_job = runtime.submit_momentum_validation(
        {"n_days": 80, "lookback": 20, "top_n": 2, "cost_bps": 10.0}
    )
    _wait_for_job(runtime, val_job.job_id)
    assistant.record_milestone("first_validation")
    focus = assistant.focus()
    assert focus.action in {FocusAction.JOURNAL, FocusAction.COMPARE, FocusAction.MARKET}


@pytest.mark.desktop
def test_journal_entry_marks_synthetic(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    assistant = NayakAssistant(runtime)
    _run_backtest(runtime)
    entries = assistant.journal_entries(limit=1)
    assert entries
    assert "SYNTHETIC" in entries[0].summary


@pytest.mark.desktop
def test_synthetic_disclaimer_copy() -> None:
    assert "Synthetic" in SYNTHETIC_SHARPE_DISCLAIMER
    assert "NIFTY" in SYNTHETIC_SHARPE_DISCLAIMER
