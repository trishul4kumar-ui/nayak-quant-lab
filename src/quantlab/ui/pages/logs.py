from __future__ import annotations

from collections import Counter

from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QPushButton

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.ui.time_format import format_ist_from_iso
from quantlab.ui.widgets.charts import DashboardStrip, LogTimelineWidget
from quantlab.ui.widgets.lab_shell import LabPageShell


class LogsPage(LabPageShell):
    _LEVELS = ("all", "info", "warning", "error", "debug")

    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Logs",
            subtitle="Structured events from the lab runtime — newest at the bottom.",
            nayak_summary="Use level chips to isolate warnings and errors during debugging.",
        )
        self._runtime = runtime
        self._active_level = "all"
        body = self.body()

        self._dash = DashboardStrip(["Total", "Info", "Warnings", "Errors"])
        body.addWidget(self._dash)

        self._timeline = LogTimelineWidget()
        body.addWidget(self._timeline)

        chip_row = QHBoxLayout()
        self._chips: dict[str, QPushButton] = {}
        for level in self._LEVELS:
            btn = QPushButton(level)
            btn.setCheckable(True)
            btn.setChecked(level == "all")
            btn.clicked.connect(lambda checked, lv=level: self._set_level(lv))
            self._chips[level] = btn
            chip_row.addWidget(btn)
        chip_row.addStretch()
        body.addLayout(chip_row)

        self.view = QPlainTextEdit()
        self.view.setReadOnly(True)
        self.view.setObjectName("log-view")
        body.addWidget(self.view, 1)
        self.refresh()

    def _set_level(self, level: str) -> None:
        self._active_level = level
        for name, btn in self._chips.items():
            btn.setChecked(name == level)
        self.refresh()

    def refresh(self) -> None:
        snapshot = self._runtime.logs.snapshot()[-400:]
        counts = Counter(
            str(row.get("level", row.get("log_level", "info"))).lower() for row in snapshot
        )
        self._dash.card(0).set_value(str(len(snapshot)))
        self._dash.card(1).set_value(str(counts.get("info", 0)))
        self._dash.card(2).set_value(
            str(counts.get("warning", 0)),
            accent="#ffa726" if counts.get("warning", 0) else "#42a5f5",
        )
        self._dash.card(3).set_value(
            str(counts.get("error", 0)),
            accent="#ef5350" if counts.get("error", 0) else "#42a5f5",
        )

        timeline: list[tuple[str, int]] = []
        for level in ("error", "warning", "info", "debug"):
            timeline.append((level, counts.get(level, 0)))
        self._timeline.set_counts(timeline)

        wanted = self._active_level
        lines: list[str] = []
        for row in snapshot:
            level = str(row.get("level", row.get("log_level", ""))).lower()
            if wanted != "all" and wanted not in level:
                continue
            ts = str(row.get("timestamp", ""))
            ts_display = format_ist_from_iso(ts) if ts else ""
            event = row.get("event") or row.get("event_dict") or row
            prefix = f"{ts_display}  " if ts_display else ""
            lines.append(f"{prefix}{level}  {event}")
        self.view.setPlainText("\n".join(lines))
        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().maximum())
