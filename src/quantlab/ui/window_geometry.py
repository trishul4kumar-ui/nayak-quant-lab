"""Keep the main window on a visible screen."""

from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget


def clamp_to_screen(widget: QWidget) -> None:
    """Resize and reposition so the window fits the primary display."""
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return
    available = screen.availableGeometry()
    width = min(max(widget.width(), 960), available.width())
    height = min(max(widget.height(), 640), available.height())
    x = widget.x()
    y = widget.y()
    if x < available.left():
        x = available.left()
    if y < available.top():
        y = available.top()
    if x + width > available.right() + 1:
        x = max(available.left(), available.right() - width + 1)
    if y + height > available.bottom() + 1:
        y = max(available.top(), available.bottom() - height + 1)
    widget.setGeometry(QRect(x, y, width, height))
