from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quantlab.app.bootstrap import bootstrap
from quantlab.ui.learn_content import unlocked_stages
from quantlab.ui.pages.test import BacktestWizardPage
from quantlab.ui.welcome import WelcomeDialog


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.mark.desktop
def test_learn_stages_unlock_with_milestones() -> None:
    assert len(unlocked_stages(set())) == 1
    assert len(unlocked_stages({"onboarding_complete"})) >= 2
    assert len(unlocked_stages({"onboarding_complete", "first_backtest"})) >= 3


@pytest.mark.desktop
def test_welcome_marks_onboarding(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    dialog = WelcomeDialog(runtime)
    dialog._stack.setCurrentIndex(dialog._stack.count() - 1)
    dialog._guided_radio.setChecked(True)
    dialog._finish()
    assert "onboarding_complete" in runtime.ui_settings.current.milestones


@pytest.mark.desktop
def test_wizard_has_three_steps(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    page = BacktestWizardPage(runtime, on_done=lambda: None)
    assert page._stack.count() == 4
