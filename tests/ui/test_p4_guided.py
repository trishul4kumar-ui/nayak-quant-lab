"""P4 — Guided Lab polish and TK-facing copy."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from quantlab.app.assistant import FocusAction, NayakAssistant
from quantlab.app.bootstrap import bootstrap
from quantlab.app.jobs import JobStatus
from quantlab.ui.learn_content import learn_progress
from quantlab.ui.pages.learn import LearnPage
from quantlab.ui.pages.test import BacktestWizardPage
from quantlab.ui.widgets.explain import EXPLANATIONS, glossary_entries
from quantlab.ui.widgets.lab_shell import data_kind_badge


def _wait_for_job(runtime, job_id: str, *, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = runtime.jobs.get(job_id)
        if job is not None and job.status in {JobStatus.COMPLETED, JobStatus.FAILED}:
            return
        time.sleep(0.05)
    raise TimeoutError(f"job {job_id} did not finish")


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.mark.desktop
def test_learn_progress_tracker(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    page = LearnPage(runtime)
    unlocked, total, _ = learn_progress(set())
    assert total == 5
    assert unlocked == 1
    assert page._progress_bar.maximum() == total
    assert page._progress_bar.value() == unlocked


@pytest.mark.desktop
def test_glossary_covers_explain_keys() -> None:
    entries = dict(glossary_entries())
    assert set(entries) == set(EXPLANATIONS)
    assert "sharpe" in entries


@pytest.mark.desktop
def test_wizard_result_has_dashboard(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    page = BacktestWizardPage(runtime, on_done=lambda: None)
    assert page._dash is not None
    assert len(page._dash.cards) == 4


@pytest.mark.desktop
def test_data_kind_badge_synthetic() -> None:
    badge = data_kind_badge("synthetic")
    assert "SYNTHETIC" in badge.text()


@pytest.mark.desktop
def test_focus_validation_copy_for_full_lab(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    assistant = NayakAssistant(runtime)
    assistant.complete_onboarding()
    job = runtime.submit_momentum_backtest(
        {"n_days": 60, "lookback": 20, "top_n": 2, "cost_bps": 10.0}
    )
    _wait_for_job(runtime, job.job_id)
    assistant.record_milestone("first_backtest")
    assistant.record_milestone("first_equity_view")
    focus = assistant.focus()
    assert focus.action is FocusAction.VALIDATION
    assert "Full Lab" in focus.action_label
