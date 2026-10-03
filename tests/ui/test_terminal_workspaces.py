"""Platform-wide terminal workspace and control-feedback contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QAbstractButton, QApplication, QLabel

from quantlab.app.bootstrap import bootstrap
from quantlab.ui.main_window import MainWindow
from quantlab.ui.widgets.lab_shell import LabPageShell
from quantlab.ui.widgets.terminal import TerminalGrid, TerminalPanel


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_every_lab_page_has_a_persisted_resizable_workspace(
    tmp_path: Path, qapp: QApplication
) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    window = MainWindow(runtime)
    qapp.processEvents()

    shell_pages = [page for page in window._pages.values() if isinstance(page, LabPageShell)]
    assert shell_pages
    assert all(page.has_terminal_layout() for page in shell_pages)
    assert window.home._lower_splitter.count() == 2
    assert window.home._lower_splitter.handleWidth() == 8
    runtime.shutdown()


def test_all_registered_pages_can_be_selected(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    window = MainWindow(runtime)
    for key, page in window._pages.items():
        window._select_nav(key)
        qapp.processEvents()
        assert window.stack.currentWidget() is window._page_shells[key]
        assert window._page_shells[key].widget() is page
    runtime.shutdown()


def test_enabled_controls_have_terminal_feedback(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    window = MainWindow(runtime)
    qapp.processEvents()
    controls = [
        button
        for button in window.findChildren(QAbstractButton)
        if button.isEnabled() and button.text().strip() and button.text() not in {"«", "»"}
    ]
    assert controls
    assert all(button.property("action_feedback_installed") for button in controls)
    runtime.shutdown()


def test_terminal_panel_focus_toggles_and_restores(qapp: QApplication) -> None:
    first = TerminalPanel("First", QLabel("first"))
    second = TerminalPanel("Second", QLabel("second"))
    grid = TerminalGrid(columns=2)
    grid.set_panels([first, second])

    first._focus.click()
    assert first._focus.text() == "Restore"
    assert first._focus.isChecked()
    assert second._focus.text() == "Focus"

    first._focus.click()
    assert first._focus.text() == "Focus"
    assert not first._focus.isChecked()
