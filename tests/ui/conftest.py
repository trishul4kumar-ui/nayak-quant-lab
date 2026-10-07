"""Release test-owned Qt windows between cases, including hidden closed windows.

Otherwise QWidget callback cycles retain entire terminals and each subsequent
application stylesheet change repolishes every earlier test's widgets.
"""

from __future__ import annotations

import gc
from collections.abc import Iterator

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

from quantlab.app.bootstrap import ApplicationRuntime


@pytest.fixture(autouse=True)
def release_test_windows() -> Iterator[None]:
    yield
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        return
    # QApplication only exposes windows in this pytest process, never the
    # user's separately running desktop. Do not invoke modal close handlers.
    for window in app.topLevelWidgets():
        runtime = getattr(window, "runtime", None) or getattr(window, "_runtime", None)
        if isinstance(runtime, ApplicationRuntime):
            runtime.shutdown()
        window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    gc.collect()
