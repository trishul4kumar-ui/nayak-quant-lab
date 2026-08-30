from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTableWidget,
    QVBoxLayout,
)

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.health import ComponentStatus
from quantlab.ui.widgets import fill_table


class SplashDialog(QDialog):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__()
        self.setWindowTitle("NAYAK QUANT LAB")
        self.setModal(True)
        self.resize(560, 420)
        layout = QVBoxLayout(self)
        title = QLabel("NAYAK QUANT LAB STARTUP")
        title.setObjectName("brand")
        layout.addWidget(title)
        meta = QLabel(
            f"Version {runtime.version}    Mode: {runtime.mode.value.upper()}    "
            f"Live Trading: {'ENABLED' if runtime.gates.live_trading else 'DISABLED'}"
        )
        layout.addWidget(meta)
        table = QTableWidget()
        rows = []
        for component in runtime.health.components:
            mark = {
                ComponentStatus.OK: "OK",
                ComponentStatus.OPTIONAL: "OPTIONAL",
                ComponentStatus.FAILED: "FAILED",
            }[component.status]
            rows.append([component.name, mark, component.detail])
        fill_table(table, ["Component", "Status", "Detail"], rows)
        layout.addWidget(table)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        if not runtime.health.research_ready():
            buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Continue (degraded)")
        layout.addWidget(buttons)
        layout.setAlignment(title, Qt.AlignmentFlag.AlignLeft)
