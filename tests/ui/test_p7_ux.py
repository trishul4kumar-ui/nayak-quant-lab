"""P7 — QuantConnect / Meridiem / Crypteria-inspired UX."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from quantlab.app.bootstrap import bootstrap
from quantlab.app.research_pipeline import PipelineStatus, build_research_pipeline
from quantlab.app.settings_store import ExperienceMode
from quantlab.app.strategy_templates import TEMPLATES, template_by_id
from quantlab.app.validation_summary import validation_two_questions
from quantlab.ui.main_window import MainWindow
from quantlab.ui.pages.test import BacktestWizardPage
from quantlab.ui.widgets.charts import DonutChartWidget, KpiCard, TargetBarWidget
from quantlab.ui.widgets.research_pipeline import ResearchPipelineStrip


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_research_pipeline_stages_order(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    stages = build_research_pipeline(runtime)
    assert [s.key for s in stages] == ["idea", "backtest", "validate", "journal", "live"]


def test_research_pipeline_passes_after_onboarding(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.milestones.append("onboarding_complete")
    stages = build_research_pipeline(runtime)
    assert stages[0].status is PipelineStatus.PASS


def test_validation_two_questions_empty(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    summary = validation_two_questions(runtime)
    assert "No validation yet" in summary.profit_line


def test_strategy_templates_default(tmp_path: Path) -> None:
    assert template_by_id("cs_momentum_v1").runnable is True
    assert len(TEMPLATES) >= 3


@pytest.mark.desktop
def test_home_pipeline_strip_builds(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    strip = ResearchPipelineStrip()
    strip.refresh(runtime)
    assert strip._stages


@pytest.mark.desktop
def test_kpi_target_bar(qapp: QApplication) -> None:
    card = KpiCard("Sharpe")
    card.set_target_progress(0.82, 1.0, headroom_label="Below target")
    assert not card._target_bar.isHidden()


@pytest.mark.desktop
def test_donut_paints(qapp: QApplication) -> None:
    chart = DonutChartWidget()
    chart.set_slices([("AAA", 0.6, "#42a5f5"), ("BBB", 0.4, "#66bb6a")])
    chart.show()
    qapp.processEvents()
    chart.repaint()


@pytest.mark.desktop
def test_test_wizard_four_steps(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    page = BacktestWizardPage(runtime, on_done=lambda: None)
    assert page._stack.count() == 4


@pytest.mark.desktop
def test_intent_card_hidden_after_pick(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.milestones.append("onboarding_complete")
    window = MainWindow(runtime)
    window.home._pick_intent("learn")
    assert runtime.ui_settings.current.onboarding_intent == "learn"
    assert not window.home._intent_frame.isVisible()
    window.close()


@pytest.mark.desktop
def test_learn_tour_tabs(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    window = MainWindow(runtime)
    assert window.learn._tour_tabs.count() == 4
    window.close()
