"""Desktop controls for the read-only Kite account observer."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from quantlab.app.bootstrap import bootstrap
from quantlab.ui.pages.broker import BrokerPage
from quantlab.ui.pages.broker_gateway_lab import BrokerGatewayLabPage


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.mark.desktop
def test_broker_wizard_describes_kite_as_read_only_observer(
    tmp_path: Path, qapp: QApplication
) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    page = BrokerPage(runtime)
    page.show()
    qapp.processEvents()
    try:
        labels = [button.text() for button in page._adapter_group.buttons()]
        assert "Zerodha Kite (read-only)" in labels
        assert "Stub" not in " ".join(labels)
    finally:
        page.close()
        runtime.shutdown()


@pytest.mark.desktop
def test_broker_wizard_maps_legacy_zerodha_preference_to_kite(
    tmp_path: Path, qapp: QApplication
) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.broker_adapter = "zerodha"
    page = BrokerPage(runtime)
    page.show()
    qapp.processEvents()
    try:
        selected = page._adapter_group.checkedButton()
        assert selected is not None
        assert selected.property("adapter_id") == "kite"
    finally:
        page.close()
        runtime.shutdown()


@pytest.mark.desktop
def test_gateway_kite_controls_acknowledge_connection_and_snapshot(
    tmp_path: Path, qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    page = BrokerGatewayLabPage(runtime)
    calls: list[str] = []
    monkeypatch.setattr(
        "quantlab.ui.pages.broker_gateway_lab.connect_payload",
        lambda *, adapter: calls.append(adapter)
        or {"state": "connected_read_only", "broker_connected": True},
    )
    monkeypatch.setattr(
        "quantlab.ui.pages.broker_gateway_lab.snapshot_payload",
        lambda: {"bundle_id": "kite-snapshot-test"},
    )
    monkeypatch.setattr(
        "quantlab.ui.pages.broker_gateway_lab.health_payload",
        lambda: {"state": "connected_read_only", "broker_connected": True},
    )
    monkeypatch.setattr("quantlab.ui.pages.broker_gateway_lab.last_run_row", lambda: None)
    page.show()
    qapp.processEvents()
    try:
        assert page._adapter.currentData() == "kite"
        QTest.mouseClick(page._connect, Qt.MouseButton.LeftButton)
        qapp.processEvents()
        assert calls == ["kite"]
        assert "connected as an account observer" in page._last_feedback

        QTest.mouseClick(page._snapshot_button, Qt.MouseButton.LeftButton)
        qapp.processEvents()
        assert calls == ["kite", "kite"]
        assert "Immutable Kite read-only snapshot" in page._last_feedback
        assert page._interaction_status.text().startswith("ACK · KITE ACCOUNT SNAPSHOT")
    finally:
        page.close()
        runtime.shutdown()


@pytest.mark.desktop
def test_gateway_exposes_safe_kite_connection_failure(
    tmp_path: Path, qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    page = BrokerGatewayLabPage(runtime)
    monkeypatch.setattr(
        "quantlab.ui.pages.broker_gateway_lab.connect_payload",
        lambda *, adapter: {"error": "kite authentication rejected (401)"},
    )
    monkeypatch.setattr(
        "quantlab.ui.pages.broker_gateway_lab.health_payload",
        lambda: {"state": "blocked", "broker_connected": False},
    )
    monkeypatch.setattr("quantlab.ui.pages.broker_gateway_lab.last_run_row", lambda: None)
    page.show()
    qapp.processEvents()
    try:
        QTest.mouseClick(page._connect, Qt.MouseButton.LeftButton)
        qapp.processEvents()
        assert "could not connect" in page._last_feedback
        assert "No account state was changed" in page._last_feedback
    finally:
        page.close()
        runtime.shutdown()
