from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton
from tests.agents.test_bear import BearFixtureProvider
from tests.agents.test_bull import ResearchFixtureProvider, snapshot

from quantlab.agents.provider import UnavailableProvider
from quantlab.app.bootstrap import bootstrap
from quantlab.ui.pages.ai_quant_desk import AiQuantDeskPage


@pytest.fixture
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize("size", [(1024, 640), (1280, 800), (1512, 982), (1920, 1080)])
def test_native_desk_inspectors_and_navigation(
    tmp_path: Path, qapp: QApplication, size: tuple[int, int]
) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    page = AiQuantDeskPage(runtime)
    try:
        page.resize(*size)
        page.show()
        qapp.processEvents()
        assert "DENIED" in page._status.text()
        assert "PLACE_LIVE_ORDER" in page._inspectors["Permissions"].toPlainText()
        assert "adapter_bound" in page._inspectors["Tools"].toPlainText()
        refresh = next(
            button
            for button in page.findChildren(QPushButton)
            if button.text() == "Refresh desk status"
        )
        QTest.mouseClick(refresh, Qt.MouseButton.LeftButton)
        page._visual.bridge.navigate("select_agent", "BEAR")
        assert page._tabs.currentIndex() == 1
        assert "No analyst runs" in page._inspectors["Bear"].toPlainText()
        assert not any("PLACE ORDER" in button.text() for button in page.findChildren(QPushButton))
    finally:
        page.close()
        runtime.shutdown()


def test_bull_button_explains_missing_provider(tmp_path: Path, qapp: QApplication) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    page = AiQuantDeskPage(runtime)
    try:
        page._provider = UnavailableProvider()
        QTest.mouseClick(page._run_button, Qt.MouseButton.LeftButton)
        assert "BLOCKED" in page._bull.task.text()
        assert "QUANT_LAB_AGENT_MODEL" in page._bull.task.text()
        assert not runtime.jobs.list_jobs()
    finally:
        page.close()
        runtime.shutdown()


def test_native_bull_run_history_and_evidence_navigation(
    tmp_path: Path,
    qapp: QApplication,
) -> None:
    runtime = bootstrap(data_dir=tmp_path / "runtime")
    page = AiQuantDeskPage(runtime)
    saved = tmp_path / "snapshot.json"
    saved.write_text(snapshot().model_dump_json())
    try:
        page._provider = ResearchFixtureProvider("NO_TRADE")
        page._snapshot_path = saved
        page._replay.setChecked(True)
        page.resize(1280, 800)
        page.show()
        qapp.processEvents()
        QTest.mouseClick(page._run_button, Qt.MouseButton.LeftButton)
        assert page._job_id is not None, page._bull.task.text()
        deadline = time.monotonic() + 10
        while page._job_id and time.monotonic() < deadline:
            QTest.qWait(25)
            page.refresh()
        assert page._job_id is None
        assert "NO_TRADE" in page._bull.memo.toPlainText()
        assert "NOT_TESTED" in page._bull.challenge.toPlainText()
        assert "SYNTHETIC" in page._bull.scope.text()
        assert page._bull.history.count() == 1
        assert "CANONICAL TOOL CALLS" in page._bull.timeline.toPlainText()
        assert "query_factor: COMPLETED" in page._bull.timeline.toPlainText()
        assert "run_validation: UNAVAILABLE" in page._bull.timeline.toPlainText()
        page._bull.search.setText("does-not-match-any-thesis")
        assert page._bull.history.item(0).isHidden()
        page._bull.search.clear()
        page._bull.history.setCurrentRow(0)
        assert page._bull.tabs.currentIndex() == 0
        import json

        evidence = json.loads(page._visual.bridge.presentation)["evidence"]
        page._visual.bridge.navigate("open_evidence", evidence[0]["artifact_hash"])
        assert page._bull.tabs.currentIndex() == 2
        assert evidence[0]["artifact_hash"] in page._bull.timeline.toPlainText()
        assert page._run_button.isEnabled() and not page._cancel_button.isEnabled()
        page._bull.evidence_splitter.setSizes([300, 600])
        page._persist_workspace_layout()
        saved_layout = runtime.ui_settings.current.terminal_layouts["ai-quant-desk"]
        assert saved_layout["bull-evidence"] == page._bull.evidence_splitter.sizes()
    finally:
        page.close()
        runtime.shutdown()


def test_native_bear_run_history_evidence_and_panel_preferences(
    tmp_path: Path,
    qapp: QApplication,
) -> None:
    import json

    runtime = bootstrap(data_dir=tmp_path / "runtime")
    page = AiQuantDeskPage(runtime)
    saved = tmp_path / "snapshot.json"
    saved.write_text(snapshot().model_dump_json())
    try:
        page._provider = UnavailableProvider()
        QTest.mouseClick(page._bear_button, Qt.MouseButton.LeftButton)
        assert "BLOCKED" in page._bear.task.text()
        assert page._tabs.currentWidget() is page._bear
        page._provider = BearFixtureProvider()
        page._snapshot_path = saved
        page._replay.setChecked(True)
        page.resize(1280, 800)
        page.show()
        qapp.processEvents()
        QTest.mouseClick(page._bear_button, Qt.MouseButton.LeftButton)
        assert page._job_id is not None, page._bear.task.text()
        assert not page._run_button.isEnabled() and not page._bear_button.isEnabled()
        deadline = time.monotonic() + 10
        while page._job_id and time.monotonic() < deadline:
            QTest.qWait(25)
            page.refresh()
        assert page._job_id is None
        assert "AVOID" in page._bear.memo.toPlainText()
        assert "Instrument eligibility: UNKNOWN" in page._bear.memo.toPlainText()
        assert "Squeeze / reversal risk" in page._bear.memo.toPlainText()
        assert page._bear.history.count() == 1 and page._bull.history.count() == 0
        page._bear.search.setText("no-such-thesis")
        assert page._bear.history.item(0).isHidden()
        page._bear.search.clear()
        page._bear.history.setCurrentRow(0)
        assert page._bear.tabs.currentIndex() == 0
        evidence = json.loads(page._visual.bridge.presentation)["evidence"]
        page._visual.bridge.navigate("open_evidence", evidence[0]["artifact_hash"])
        assert page._bear.tabs.currentIndex() == 2
        assert page._tabs.currentWidget() is page._bear
        assert evidence[0]["artifact_hash"] in page._bear.timeline.toPlainText()
        page._bear.evidence_splitter.setSizes([300, 600])
        page._persist_workspace_layout()
        assert runtime.ui_settings.current.terminal_layouts["ai-quant-desk"]["bear-evidence"] == (
            page._bear.evidence_splitter.sizes()
        )
        assert page._run_button.isEnabled() and page._bear_button.isEnabled()
    finally:
        page.close()
        runtime.shutdown()
