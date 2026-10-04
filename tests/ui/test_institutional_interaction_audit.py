"""End-to-end interaction contract for the desktop terminal.

This intentionally drives Qt controls instead of calling page methods directly.  It
protects the user-facing promise that a click either changes state, navigates, or
clearly acknowledges why it cannot proceed.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QToolButton

from quantlab.app.bootstrap import bootstrap
from quantlab.app.jobs import JobStatus
from quantlab.app.settings_store import ExperienceMode
from quantlab.ui.main_window import MainWindow
from quantlab.ui.widgets.command_palette import CommandPalette


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _click_nav(window: MainWindow, key: str) -> None:
    row = next(index for index, mapped in enumerate(window._row_to_key) if mapped == key)
    index = window.nav.model().index(row, 0)
    point = window.nav.visualRect(index).center()
    QTest.mouseClick(window.nav.viewport(), Qt.MouseButton.LeftButton, pos=point)


@pytest.mark.desktop
def test_terminal_controls_have_visible_outcomes(tmp_path: Path, qapp: QApplication) -> None:
    """Exercise navigation, search, tabs, actions, jobs, persistence, and safety UI."""
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.experience_mode = ExperienceMode.FULL
    runtime.ui_settings.save()
    window = MainWindow(runtime)
    window.resize(1440, 920)
    window.show()
    qapp.processEvents()

    try:
        # Actual sidebar click changes the active page.
        _click_nav(window, "data")
        qapp.processEvents()
        assert window.stack.currentWidget() is window._page_shells["data"]

        # The page-local rail makes a click acknowledgement visible where work happens.
        data = window.data
        technical = next(
            button for button in data.findChildren(QToolButton) if "Technical" in button.text()
        )
        QTest.mouseClick(technical, Qt.MouseButton.LeftButton)
        qapp.processEvents()
        assert technical.text().endswith("▾")
        assert data._interaction_status.text().startswith("ACK · TECHNICAL DETAILS")

        # A data-tab click switches content, instead of presenting a decorative tab row.
        QTest.mouseClick(
            data._tabs.tabBar(),
            Qt.MouseButton.LeftButton,
            pos=data._tabs.tabBar().tabRect(1).center(),
        )
        qapp.processEvents()
        assert data._tabs.currentIndex() == 1

        # ⌘K/command-search opens the real modal palette and activates its first result.
        window._command_search.setText("backtest")

        def accept_palette() -> None:
            dialog = QApplication.activeModalWidget()
            assert isinstance(dialog, CommandPalette)
            QTest.keyClick(dialog._search, Qt.Key.Key_Return)

        QTimer.singleShot(60, accept_palette)
        window._open_command_palette()
        qapp.processEvents()
        assert window.stack.currentWidget() is window._page_shells["backtests"]

        # A real click queues the synthetic job and exposes cancellable progress.
        backtest = window.backtest
        QTest.mouseClick(backtest.run_btn, Qt.MouseButton.LeftButton)
        qapp.processEvents()
        assert backtest._job is not None
        assert backtest.cancel_btn.isEnabled()
        assert "progress=" in backtest.status.text() or "Queued" in backtest.status.text()

        deadline = time.time() + 30
        while time.time() < deadline and backtest._job is not None:
            qapp.processEvents()
            job = backtest._job
            if job is not None:
                current = runtime.jobs.get(job.job_id)
                if current is not None and current.status in {
                    JobStatus.COMPLETED,
                    JobStatus.FAILED,
                    JobStatus.CANCELLED,
                }:
                    backtest.poll()
            QTest.qWait(25)
        assert backtest._job is None
        assert runtime.ledger.list_runs()
        assert backtest.run_btn.isEnabled()

        # Comparing the generated result renders a meaningful table/chart rather than a no-op.
        _click_nav(window, "compare")
        qapp.processEvents()
        assert window.compare._picker.selectedItems()
        QTest.mouseClick(window.compare._compare_btn, Qt.MouseButton.LeftButton)
        qapp.processEvents()
        assert window.compare._table.rowCount() > 0

        # Terminal panel focus has a reversible outcome.
        _click_nav(window, "backtests")
        qapp.processEvents()
        focus = backtest._terminal._panels[0]._focus
        QTest.mouseClick(focus, Qt.MouseButton.LeftButton)
        assert focus.text() == "Restore"
        QTest.mouseClick(focus, Qt.MouseButton.LeftButton)
        assert focus.text() == "Focus"

        # Settings save is deliberately disabled until a change is made, then persists.
        _click_nav(window, "settings")
        qapp.processEvents()
        settings = window.settings
        settings._name_input.setFocus()
        QTest.keyClicks(settings._name_input, " Institutional")
        assert settings._name_save.isEnabled()
        QTest.mouseClick(settings._name_save, Qt.MouseButton.LeftButton)
        qapp.processEvents()
        assert runtime.ui_settings.current.tk_display_name.endswith("Institutional")

        # Offline research assistance responds locally; no broker-write path is invoked.
        _click_nav(window, "ai")
        qapp.processEvents()
        ai = window.ai_research
        QTest.keyClicks(ai._input, "Explain Sharpe")
        assert ai._send_button.isEnabled()
        QTest.mouseClick(ai._send_button, Qt.MouseButton.LeftButton)
        qapp.processEvents()
        assert ai._transcript.count() >= 2
        assert runtime.gates.live_trading is False
        assert runtime.gates.broker_write_enabled is False
    finally:
        window.close()
        runtime.shutdown()
