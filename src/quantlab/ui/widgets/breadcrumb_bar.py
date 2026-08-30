"""Reusable breadcrumb with clickable section toggle."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class BreadcrumbBar(QWidget):
    """Section (click to collapse) / page label."""

    def __init__(
        self,
        *,
        on_section_click: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_section_click = on_section_click
        self.setObjectName("breadcrumb")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(4)
        self._section_btn = QPushButton()
        self._section_btn.setFlat(True)
        self._section_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._section_btn.setStyleSheet(
            "QPushButton { color: #42a5f5; font-size: 12px; text-align: left; "
            "border: none; padding: 0; }"
            "QPushButton:hover { text-decoration: underline; }"
        )
        self._section_btn.clicked.connect(self._section_clicked)
        self._sep = QLabel("/")
        self._sep.setStyleSheet("color: #6b7080; font-size: 12px;")
        self._page = QLabel()
        self._page.setStyleSheet("color: #6b7080; font-size: 12px;")
        layout.addWidget(self._section_btn)
        layout.addWidget(self._sep)
        layout.addWidget(self._page)
        layout.addStretch()
        self.set_parts("", "")

    def set_parts(self, section: str, page: str) -> None:
        has_section = bool(section)
        self._section_btn.setVisible(has_section)
        self._sep.setVisible(has_section)
        if has_section:
            self._section_btn.setText(section)
            self._section_btn.setToolTip("Click to collapse or expand this nav section")
        self._page.setText(page)

    def _section_clicked(self) -> None:
        if self._on_section_click is not None:
            self._on_section_click()
