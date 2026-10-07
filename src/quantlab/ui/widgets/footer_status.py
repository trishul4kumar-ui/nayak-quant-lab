"""Color-coded footer status chips."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QStatusBar, QWidget

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.pulse import status_tone
from quantlab.app.settings_store import UiTheme


def _chip_tones(theme: UiTheme) -> dict[str, tuple[str, str]]:
    if theme is UiTheme.LIGHT:
        return {
            "ok": ("#d4ede8", "#1b6b5c"),
            "warn": ("#fff3e0", "#b86e00"),
            "bad": ("#fde8e8", "#c62828"),
            "neutral": ("#f0ebe3", "#5c574f"),
        }
    return {
        "ok": ("#1a2e28", "#26a69a"),
        "warn": ("#2e2a1a", "#ffb74d"),
        "bad": ("#2e1a1a", "#ef5350"),
        "neutral": ("#252932", "#9aa1ad"),
    }


class _StatusChip(QFrame):
    clicked = Signal(str)

    def __init__(
        self,
        label: str,
        value: str,
        *,
        tone: str,
        nav_key: str = "",
        theme: UiTheme = UiTheme.DARK,
    ) -> None:
        super().__init__()
        self._nav_key = nav_key
        if nav_key:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._label = label
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        self._text = QLabel()
        layout.addWidget(self._text)
        self.update_value(value, tone=tone, theme=theme)

    def update_value(self, value: str, *, tone: str, theme: UiTheme) -> None:
        self._text.setText(f"{self._label}: {value}")
        tones = _chip_tones(theme)
        bg, fg = tones.get(tone, tones["neutral"])
        self.setStyleSheet(
            f"background: {bg}; color: {fg}; padding: 2px 8px; "
            "border-radius: 4px; font-size: 11px; font-weight: 600;"
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._nav_key:
            self.clicked.emit(self._nav_key)
        super().mousePressEvent(event)


class FooterStatusBar(QStatusBar):
    """Slim footer — detailed ops status lives on Home Pulse."""

    chip_clicked = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("footerStatus")
        self._host = QWidget()
        self._host.setObjectName("footerStatusHost")
        self._layout = QHBoxLayout(self._host)
        self._layout.setContentsMargins(4, 0, 4, 0)
        self._layout.setSpacing(6)
        self._chips: dict[str, _StatusChip] = {}
        self._hint = QLabel("System · Data · Jobs → Home Pulse")
        self._layout.addWidget(self._hint)
        self._layout.addStretch()
        self.addWidget(self._host, 1)

    def update_from_runtime(self, runtime: ApplicationRuntime, *, mode_label: str) -> None:
        status = runtime.status
        theme = runtime.ui_settings.current.theme
        hint_color = "#5c574f" if theme is UiTheme.LIGHT else "#6b7080"
        chips = [
            ("MODE", mode_label, "neutral", ""),
            (
                "LIVE",
                status.live_trading,
                status_tone("LIVE", status.live_trading),
                "broker",
            ),
            (
                "BROKER",
                status.broker,
                status_tone("BROKER", status.broker),
                "broker",
            ),
            (
                "KITE DATA",
                runtime.live_market.status,
                "ok" if runtime.live_market.status == "LIVE QUOTES" else "warn",
                "market",
            ),
        ]
        for label, value, tone, nav_key in chips:
            chip = self._chips.get(label)
            if chip is None:
                chip = _StatusChip(label, value, tone=tone, nav_key=nav_key, theme=theme)
                self._chips[label] = chip
                if nav_key:
                    chip.clicked.connect(self.chip_clicked.emit)
                self._layout.insertWidget(len(self._chips) - 1, chip)
            else:
                chip.update_value(value, tone=tone, theme=theme)
            if label == "BROKER":
                chip.setToolTip("Broker account session, separate from Kite market-data access")
            elif label == "KITE DATA":
                chip.setToolTip("Kite quote feed only. Data connectivity never enables trading.")
        self._hint.setStyleSheet(f"color: {hint_color}; font-size: 11px;")
