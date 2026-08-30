"""Scroll wrapper for lab pages that may exceed the viewport."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QWidget


def wrap_page_scroll(page: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setObjectName("pageScroll")
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    scroll.setWidget(page)
    return scroll
