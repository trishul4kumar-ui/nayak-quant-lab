"""Desktop GUI smoke tests. Requires PySide6 and an offscreen Qt platform."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QUANT_LAB_SKIP_SPLASH", "1")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from quantlab.app.bootstrap import bootstrap
from quantlab.app.jobs import JobStatus
from quantlab.app.settings_store import ExperienceMode
from quantlab.ui.main_window import MainWindow


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _nav_labels(window: MainWindow) -> list[str]:
    """Strip keyboard shortcut hints from sidebar item text."""
    raw = [window.nav.item(i).text() for i in range(window.nav.count())]
    return [label.split("   ")[0] for label in raw]


@pytest.mark.desktop
def test_main_window_guided_mode_starts(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    window = MainWindow(runtime)
    window.show()
    qapp.processEvents()
    labels = _nav_labels(window)
    assert "Home" in labels
    assert "Learn" in labels
    assert "Test" in labels
    assert "Journal" in labels
    assert "RESEARCH" in window._greeting_chip.text()
    assert "TK" in window.home._greeting.text()
    assert "NAYAK QUANT LAB" in window.windowTitle()
    assert "RESEARCH" in window.windowTitle()
    window.close()
    assert runtime.is_closed


@pytest.mark.desktop
def test_nayak_says_guided_only(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    window = MainWindow(runtime)
    window.show()
    qapp.processEvents()
    assert window.home._focus_frame.isVisible()
    runtime.ui_settings.current.experience_mode = ExperienceMode.FULL
    window.home.refresh()
    qapp.processEvents()
    assert not window.home._focus_frame.isVisible()
    runtime.ui_settings.current.experience_mode = ExperienceMode.GUIDED
    window.home.refresh()
    qapp.processEvents()
    assert window.home._focus_frame.isVisible()
    window.close()


@pytest.mark.desktop
def test_main_window_full_mode_nav(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.experience_mode = ExperienceMode.FULL
    window = MainWindow(runtime)
    window.show()
    qapp.processEvents()
    labels = _nav_labels(window)
    assert "Data" in labels
    assert "Validation" in labels
    assert "Compare" in labels
    assert "Market" in labels
    assert "Alpha Lab" in labels
    assert "Ensemble Lab" in labels
    assert "Execution Lab" in labels
    assert "Research Control" in labels
    assert "Discovery Lab" in labels
    assert "Knowledge Lab" in labels
    assert "Capital Lab" in labels
    assert "Paper OMS Lab" in labels
    assert "Monitoring Lab" in labels
    assert "TCA & Capacity Lab" in labels
    assert "Econometrics Lab" in labels
    assert "Validation & Certification Lab" in labels
    assert "Shadow Trading Lab" in labels
    assert "Safety & Control Lab" in labels
    assert "Operations Control Lab" in labels
    assert "Certification & Promotion Lab" in labels
    assert "Broker Gateway Lab" in labels
    assert "Real-Time Data Lab" in labels
    assert "Real-Time Decision Lab" in labels
    assert "Digital Twin / Shadow Lab" in labels
    data_row = next(i for i in range(window.nav.count()) if _nav_labels(window)[i] == "Data")
    window.nav.setCurrentRow(data_row)
    qapp.processEvents()
    data_tabs = [window.data._tabs.tabText(i) for i in range(window.data._tabs.count())]
    assert "Quality" in data_tabs
    assert "Security master" in data_tabs
    assert "Corporate actions" in data_tabs
    assert "Calendar" in data_tabs
    assert "Universe" in data_tabs
    market_row = next(i for i in range(window.nav.count()) if _nav_labels(window)[i] == "Market")
    window.nav.setCurrentRow(market_row)
    qapp.processEvents()
    assert window.market.models.rowCount() >= 1
    shadow_row = next(
        i for i in range(window.nav.count()) if _nav_labels(window)[i] == "Shadow Trading Lab"
    )
    window.nav.setCurrentRow(shadow_row)
    qapp.processEvents()
    page = window.shadow_lab
    badge_text = " ".join(widget.text() for widget in page.findChildren(QLabel) if widget.text())
    assert "PAPER" in badge_text
    assert "SHADOW" in badge_text
    assert "LIVE DISABLED" in badge_text
    assert "NO BROKER ROUTING" in badge_text
    assert "BROKER CONFIRMED" not in badge_text
    assert "ORDER SENT" not in badge_text
    actions = [btn.text() for btn in page.findChildren(QPushButton)]
    assert "RUN SHADOW" in actions
    assert not any(text == "LIVE" or text.startswith("SEND") for text in actions)
    safety_row = next(
        i for i in range(window.nav.count()) if _nav_labels(window)[i] == "Safety & Control Lab"
    )
    window.nav.setCurrentRow(safety_row)
    qapp.processEvents()
    safety_page = window.safety_lab
    safety_badge = " ".join(
        widget.text() for widget in safety_page.findChildren(QLabel) if widget.text()
    )
    assert "LIVE DISABLED" in safety_badge
    assert "BROKER CONFIRMED" not in safety_badge
    assert "ORDER SENT" not in safety_badge
    safety_actions = [btn.text() for btn in safety_page.findChildren(QPushButton)]
    assert "RUN SAFETY" in safety_actions
    assert not any(text == "LIVE" or text.startswith("SEND") for text in safety_actions)
    ops_row = next(
        i for i in range(window.nav.count()) if _nav_labels(window)[i] == "Operations Control Lab"
    )
    window.nav.setCurrentRow(ops_row)
    qapp.processEvents()
    ops_page = window.ops_lab
    ops_badge = " ".join(widget.text() for widget in ops_page.findChildren(QLabel) if widget.text())
    assert "LIVE DISABLED" in ops_badge
    ops_actions = [btn.text() for btn in ops_page.findChildren(QPushButton)]
    assert "RUN DOCTOR" in ops_actions
    assert not any(text == "LIVE" or text.startswith("SEND") for text in ops_actions)
    promote_row = next(
        i
        for i in range(window.nav.count())
        if _nav_labels(window)[i] == "Certification & Promotion Lab"
    )
    window.nav.setCurrentRow(promote_row)
    qapp.processEvents()
    promote_page = window.promotion_lab
    promote_badge = " ".join(
        widget.text() for widget in promote_page.findChildren(QLabel) if widget.text()
    )
    assert "LIVE DISABLED" in promote_badge
    promote_actions = [btn.text() for btn in promote_page.findChildren(QPushButton)]
    assert "RUN CERTIFICATION" in promote_actions
    assert not any(text == "LIVE" or text.startswith("SEND") for text in promote_actions)
    gateway_row = next(
        i for i in range(window.nav.count()) if _nav_labels(window)[i] == "Broker Gateway Lab"
    )
    window.nav.setCurrentRow(gateway_row)
    qapp.processEvents()
    gateway_page = window.broker_gateway_lab
    gateway_badge = " ".join(
        widget.text() for widget in gateway_page.findChildren(QLabel) if widget.text()
    )
    assert "LIVE DISABLED" in gateway_badge
    assert "READ-ONLY" in gateway_badge
    assert "NO ORDER ROUTING" in gateway_badge
    gateway_actions = [btn.text() for btn in gateway_page.findChildren(QPushButton)]
    assert "RUN SNAPSHOT" in gateway_actions
    assert not any(text == "LIVE" or text.startswith("SEND") for text in gateway_actions)
    rt_data_row = next(
        i for i in range(window.nav.count()) if _nav_labels(window)[i] == "Real-Time Data Lab"
    )
    window.nav.setCurrentRow(rt_data_row)
    qapp.processEvents()
    rt_data_page = window.realtime_data_lab
    rt_data_badge = " ".join(
        widget.text() for widget in rt_data_page.findChildren(QLabel) if widget.text()
    )
    assert "LIVE DISABLED" in rt_data_badge
    assert "OBSERVE-ONLY" in rt_data_badge
    rt_data_actions = [btn.text() for btn in rt_data_page.findChildren(QPushButton)]
    assert "RUN SNAPSHOT" in rt_data_actions
    assert not any(text == "LIVE" or text.startswith("SEND") for text in rt_data_actions)
    rt_decision_row = next(
        i for i in range(window.nav.count()) if _nav_labels(window)[i] == "Real-Time Decision Lab"
    )
    window.nav.setCurrentRow(rt_decision_row)
    qapp.processEvents()
    rt_decision_page = window.realtime_decision_lab
    rt_decision_badge = " ".join(
        widget.text() for widget in rt_decision_page.findChildren(QLabel) if widget.text()
    )
    assert "LIVE DISABLED" in rt_decision_badge
    assert "DECISION ≠ ORDER" in rt_decision_badge
    rt_decision_actions = [btn.text() for btn in rt_decision_page.findChildren(QPushButton)]
    assert "RUN DECISION" in rt_decision_actions
    assert not any(text == "LIVE" or text.startswith("SEND") for text in rt_decision_actions)
    twin_row = next(
        i
        for i in range(window.nav.count())
        if _nav_labels(window)[i] == "Digital Twin / Shadow Lab"
    )
    window.nav.setCurrentRow(twin_row)
    qapp.processEvents()
    twin_page = window.digital_twin_lab
    twin_badge = " ".join(
        widget.text() for widget in twin_page.findChildren(QLabel) if widget.text()
    )
    assert "LIVE DISABLED" in twin_badge
    assert "SHADOW ONLY" in twin_badge
    assert "ZERO BROKER WRITE" in twin_badge
    twin_actions = [btn.text() for btn in twin_page.findChildren(QPushButton)]
    assert "RUN SHADOW" in twin_actions
    assert not any(text == "LIVE" or text.startswith("SEND") for text in twin_actions)
    window.close()


@pytest.mark.desktop
def test_backtest_from_ui_saves_experiment(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.experience_mode = ExperienceMode.FULL
    window = MainWindow(runtime)
    window.show()
    qapp.processEvents()
    window.backtest._start()
    deadline = time.time() + 30
    while time.time() < deadline:
        qapp.processEvents()
        job = window.backtest._job
        if job is None and runtime.ledger.list_runs():
            break
        if job is not None:
            current = runtime.jobs.get(job.job_id)
            if current is not None and current.status in {
                JobStatus.COMPLETED,
                JobStatus.FAILED,
            }:
                window.backtest.poll()
                break
        time.sleep(0.05)
    window.backtest.poll()
    runs = runtime.ledger.list_runs()
    assert runs, "backtest should append to the experiment ledger"
    assert runs[-1].integrity.get("look_ahead_bias") == "pass"
    assert runs[-1].application_version
    window.close()
