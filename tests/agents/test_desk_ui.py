from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

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
