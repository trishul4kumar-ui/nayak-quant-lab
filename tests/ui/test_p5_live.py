"""P5 — Live / safety UX."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from quantlab.app.bootstrap import bootstrap
from quantlab.app.live_ops import execution_monitor_rows, live_gate_rows, target_holdings
from quantlab.core.errors import SafetyError
from quantlab.ui.pages.broker import BrokerPage
from quantlab.ui.widgets.live_confirm_dialog import LiveConfirmDialog


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.mark.desktop
def test_live_gate_rows_fail_closed(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    rows = live_gate_rows(runtime.gates)
    assert len(rows) == 8
    assert not all(met for _, met in rows)


@pytest.mark.desktop
def test_broker_wizard_three_steps(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    page = BrokerPage(runtime)
    assert page._stack.count() == 3


@pytest.mark.desktop
def test_broker_paper_setup_persists(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    page = BrokerPage(runtime)
    page._step = 1
    page._stack.setCurrentIndex(1)
    page._no_secrets.setChecked(True)
    page._go_next()
    prefs = runtime.ui_settings.current
    assert prefs.broker_wizard_complete is True
    assert prefs.broker_adapter == "paper"


@pytest.mark.desktop
def test_paper_holdings_after_broker_wizard(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    prefs = runtime.ui_settings.current
    prefs.broker_adapter = "paper"
    prefs.broker_wizard_complete = True
    runtime.ui_settings.save()
    rows, note = target_holdings(runtime)
    assert rows
    assert "paper" in note.lower() or "demo" in note.lower()


@pytest.mark.desktop
def test_live_confirm_dialog_blocks_without_ack(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    dialog = LiveConfirmDialog(runtime)
    ok_btn = dialog._buttons.button(dialog._buttons.StandardButton.Ok)
    assert not ok_btn.isEnabled()


@pytest.mark.desktop
def test_request_live_still_blocked(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    with pytest.raises(SafetyError):
        runtime.try_enable_live()


@pytest.mark.desktop
def test_execution_monitor_empty_without_runs(tmp_path: Path) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    rows, note = execution_monitor_rows(runtime)
    assert rows == []
    assert "execution" in note.lower()
