"""Desktop visual language — dark and light themes."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QApplication

from quantlab.app.settings_store import UiTheme


@dataclass(frozen=True)
class ChartPalette:
    background: str
    muted: str
    grid: str
    foreground: str


_CHART_PALETTE = ChartPalette(
    background="#1c1f26",
    muted="#6b7080",
    grid="#353945",
    foreground="#e8eaed",
)

_ACTIVE_UI_THEME = UiTheme.DARK


def chart_palette() -> ChartPalette:
    return _CHART_PALETTE


def active_ui_theme() -> UiTheme:
    return _ACTIVE_UI_THEME


def _set_chart_palette(theme: UiTheme) -> None:
    global _CHART_PALETTE
    if theme is UiTheme.LIGHT:
        _CHART_PALETTE = ChartPalette(
            background="#f7f5f2",
            muted="#5c574f",
            grid="#ddd6ce",
            foreground="#2c2825",
        )
    else:
        _CHART_PALETTE = ChartPalette(
            background="#1c1f26",
            muted="#6b7080",
            grid="#353945",
            foreground="#e8eaed",
        )


DARK_STYLESHEET = """
QWidget {
    background: #1c1f26;
    color: #e8eaed;
    font-size: 14px;
}
QMainWindow, QDialog {
    background: #1c1f26;
}
QFrame {
    border: none;
}
QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
QWidget#learnScrollBody {
    background: transparent;
}
QListWidget {
    background: #1c1f26;
    border: none;
    padding: 8px 0;
    outline: none;
}
QListWidget::item {
    padding: 4px 10px;
    color: #b4b8c2;
    border: none;
}
QListWidget::item:selected {
    background: #2a3144;
    color: #f2f4f8;
}
QLabel#brand {
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 1px;
    color: #c9a96e;
}
QLabel#tkGreeting {
    font-size: 22px;
    font-weight: 500;
    color: #f2f4f8;
}
QLabel#nayakVoice {
    font-size: 14px;
    color: #9aa0a8;
}
QLabel#nayakLabel {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    color: #6ba3b8;
}
QLabel#contextStrip {
    font-size: 13px;
    color: #6ba3b8;
    padding: 6px 12px;
    background: #252932;
    border: none;
    border-radius: 6px;
}
QWidget#contextHost {
    background: #252932;
    border: none;
    border-radius: 6px;
}
QLabel#modeBadge {
    padding: 4px 10px;
    background: #243044;
    color: #c9d4e8;
    font-weight: 600;
}
QLabel#modeBadgeLive {
    padding: 4px 10px;
    background: #9b3b3b;
    color: #ffe8e8;
    font-weight: 700;
}
QLabel#liveBanner {
    background: #9b3b3b;
    color: #fff;
    font-weight: 700;
    padding: 8px;
    qproperty-alignment: AlignCenter;
}
QLabel#navHeader {
    color: #6b7080;
    font-size: 11px;
    font-weight: 600;
    padding: 12px 16px 4px 16px;
}
QListWidget#nav-list {
    background: #1c1f26;
    border: none;
    padding: 4px 0;
    outline: none;
}
QListWidget#nav-list QScrollBar:vertical {
    width: 10px;
    margin: 2px 2px 2px 0;
    background: transparent;
}
QListWidget#nav-list QScrollBar::handle:vertical {
    background: #3d4450;
    border-radius: 4px;
    min-height: 28px;
}
QListWidget#nav-list QScrollBar::handle:vertical:hover {
    background: #6ba3b8;
}
QListWidget#nav-list QScrollBar::add-line:vertical,
QListWidget#nav-list QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollArea#pageScroll {
    background: transparent;
    border: none;
}
QScrollArea#pageScroll QScrollBar:vertical {
    width: 10px;
    background: #1c1f26;
}
QScrollArea#pageScroll QScrollBar::handle:vertical {
    background: #3d4450;
    border-radius: 4px;
    min-height: 28px;
}
QScrollArea#pageScroll QScrollBar::handle:vertical:hover {
    background: #6ba3b8;
}
QScrollArea#pageScroll QScrollBar::add-line:vertical,
QScrollArea#pageScroll QScrollBar::sub-line:vertical {
    height: 0;
}
QWidget#navHost {
    border-right: none;
}
QWidget#navHostLive {
    background: #2a1818;
    border-right: none;
}
QPushButton#navToggle {
    padding: 2px 4px;
    font-size: 12px;
    min-width: 24px;
}
QPushButton {
    background: #2c333f;
    border: none;
    padding: 6px 14px;
    border-radius: 4px;
}
QPushButton:hover {
    background: #394152;
}
QPushButton#primary {
    background: #2f5f73;
    border: none;
    color: #f2f4f8;
    font-weight: 600;
}
QPushButton#modeToggle {
    padding: 4px 12px;
    font-size: 12px;
}
QPushButton#modeToggle:checked {
    background: #2f5f73;
    border: none;
    color: #f2f4f8;
}
QPushButton:disabled {
    color: #6b7080;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QComboBox {
    background: #252932;
    border: none;
    padding: 6px 10px;
    border-radius: 4px;
}
QLineEdit#navSearch {
    font-size: 12px;
    padding: 4px 8px;
    margin: 0 4px;
}
QTableWidget {
    background: #1c1f26;
    alternate-background-color: #1c1f26;
    gridline-color: transparent;
    selection-background-color: #2a3144;
    border: none;
    outline: none;
    font-family: "SF Mono", Menlo, Monaco, monospace;
    font-size: 13px;
}
QHeaderView::section {
    background: #252932;
    color: #9aa1ad;
    border: none;
    padding: 6px;
}
QFrame#learnCard {
    background: #252932;
    border: none;
    border-radius: 8px;
}
QProgressBar {
    border: none;
    background: #252932;
    text-align: center;
    border-radius: 4px;
}
QProgressBar::chunk {
    background: #6ba3b8;
}
QStatusBar {
    background: #1c1f26;
    color: #9aa1ad;
    border: none;
}
QSplitter::handle {
    background: transparent;
}
QSplitter::handle:horizontal {
    width: 4px;
}
QSplitter::handle:vertical {
    height: 4px;
}
QFrame#card {
    background: #252932;
    border: none;
    border-radius: 6px;
}
QFrame#kpiCard {
    background: #252932;
    border: none;
    border-radius: 6px;
}
QWidget#dashboardStrip {
    background: transparent;
}
QWidget#sparkline, QWidget#multi-series-chart, QWidget#drawdown-chart,
QWidget#bar-chart, QWidget#scatter-chart, QWidget#equity-curve {
    background: transparent;
    border: none;
    border-radius: 6px;
}
QFrame#focusCard {
    background: #252932;
    border: none;
    border-radius: 8px;
}
QFrame#journalCard {
    background: #2a2620;
    border: none;
    border-radius: 8px;
}
QListWidget#journalList {
    background: #2a2620;
    border: none;
    border-radius: 8px;
    padding: 8px;
}
QListWidget#journalList::item {
    padding: 10px;
    border-radius: 4px;
    color: #c9a96e;
}
QListWidget#journalList::item:selected {
    background: #3d3830;
    color: #f2f4f8;
}
QFrame#pulseCard {
    background: #252932;
    border: none;
    border-radius: 8px;
}
QFrame#pulseCardItem {
    border: none;
    border-radius: 6px;
}
QFrame#terminalPanel {
    background: #252932;
    border: none;
    border-radius: 6px;
}
QFrame#terminalPanel:focus-within {
    background: #2a3144;
}
QFrame#chatUser {
    background: #2a3144;
    border-radius: 8px;
    padding: 8px;
}
QFrame#chatNayak {
    background: #252932;
    border: none;
    border-radius: 8px;
    padding: 8px;
}
QFrame#emptyState {
    background: #111318;
    border: none;
    border-radius: 8px;
}
QFrame#runningBanner {
    background: #1a2433;
    border: 1px solid #2a4a6a;
    border-radius: 6px;
}
QFrame#nayakTip {
    background: #252932;
    border: none;
    border-radius: 8px;
}
QTabWidget::pane {
    border: none;
    border-radius: 6px;
    top: -1px;
}
QTabBar::tab {
    background: #252932;
    padding: 6px 12px;
    margin-right: 2px;
    border: none;
}
QTabBar::tab:selected {
    background: #2a3144;
}
QPushButton:focus {
    outline: 2px solid #6ba3b8;
    outline-offset: 1px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus, QComboBox:focus {
    outline: 2px solid #6ba3b8;
    outline-offset: 0px;
}
QTableWidget:focus {
    outline: 2px solid #6ba3b8;
}
QListWidget#nav-list:focus {
    outline: 2px solid #6ba3b8;
}
QFrame#focusCard:focus-within {
    outline: 2px solid #6ba3b8;
    outline-offset: 0px;
}
QPlainTextEdit#log-view {
    font-family: "SF Mono", Menlo, Monaco, monospace;
    font-size: 12px;
    background: #252932;
    border: none;
}
"""

LIGHT_STYLESHEET = """
QWidget {
    background: #f7f5f2;
    color: #2c2825;
    font-size: 14px;
}
QMainWindow, QDialog {
    background: #f7f5f2;
}
QFrame {
    border: none;
}
QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
QWidget#learnScrollBody {
    background: transparent;
}
QListWidget {
    background: #ffffff;
    border: none;
    padding: 8px 0;
    outline: none;
}
QListWidget::item {
    padding: 4px 10px;
    color: #4a4540;
    border: none;
}
QListWidget::item:selected {
    background: #dce8ee;
    color: #1a1a1a;
}
QLabel#brand {
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 1px;
    color: #8a6d3b;
}
QLabel#tkGreeting {
    font-size: 22px;
    font-weight: 500;
    color: #2c2825;
}
QLabel#nayakVoice {
    font-size: 14px;
    color: #5c574f;
}
QLabel#nayakLabel {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    color: #3d7a8c;
}
QLabel#contextStrip {
    font-size: 13px;
    color: #3d7a8c;
    padding: 6px 12px;
    background: #eef4f7;
    border: none;
    border-radius: 6px;
}
QLabel#modeBadge {
    padding: 4px 10px;
    background: #dce8ee;
    color: #2c4a5a;
    font-weight: 600;
}
QLabel#modeBadgeLive {
    padding: 4px 10px;
    background: #c44;
    color: #fff;
    font-weight: 700;
}
QLabel#liveBanner {
    background: #c44;
    color: #fff;
    font-weight: 700;
    padding: 8px;
    qproperty-alignment: AlignCenter;
}
QPushButton {
    background: #ffffff;
    border: none;
    padding: 6px 14px;
    border-radius: 4px;
    color: #2c2825;
}
QPushButton:hover {
    background: #f0ebe3;
}
QPushButton#primary {
    background: #3d7a8c;
    border: none;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#modeToggle:checked {
    background: #3d7a8c;
    border: none;
    color: #ffffff;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QComboBox {
    background: #ffffff;
    border: none;
    padding: 6px 10px;
    border-radius: 4px;
    color: #2c2825;
}
QLineEdit#navSearch {
    font-size: 12px;
    padding: 4px 8px;
    margin: 0 4px;
}
QListWidget#nav-list {
    background: #ffffff;
    border: none;
    padding: 4px 0;
    outline: none;
}
QListWidget#nav-list QScrollBar:vertical {
    width: 10px;
    margin: 2px 2px 2px 0;
    background: transparent;
}
QListWidget#nav-list QScrollBar::handle:vertical {
    background: #c8c0b8;
    border-radius: 4px;
    min-height: 28px;
}
QListWidget#nav-list QScrollBar::handle:vertical:hover {
    background: #3d7a8c;
}
QListWidget#nav-list QScrollBar::add-line:vertical,
QListWidget#nav-list QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollArea#pageScroll {
    background: transparent;
    border: none;
}
QScrollArea#pageScroll QScrollBar:vertical {
    width: 10px;
    background: #f7f5f2;
}
QScrollArea#pageScroll QScrollBar::handle:vertical {
    background: #c8c0b8;
    border-radius: 4px;
    min-height: 28px;
}
QScrollArea#pageScroll QScrollBar::handle:vertical:hover {
    background: #3d7a8c;
}
QScrollArea#pageScroll QScrollBar::add-line:vertical,
QScrollArea#pageScroll QScrollBar::sub-line:vertical {
    height: 0;
}
QWidget#navHost {
    border-right: none;
}
QWidget#navHostLive {
    background: #f5e8e8;
    border-right: none;
}
QPushButton#navToggle {
    padding: 2px 4px;
    font-size: 12px;
    min-width: 24px;
}
QTableWidget {
    background: #ffffff;
    alternate-background-color: #ffffff;
    gridline-color: transparent;
    selection-background-color: #dce8ee;
    border: none;
    outline: none;
    font-family: "SF Mono", Menlo, Monaco, monospace;
    font-size: 13px;
}
QTableWidget:focus {
    outline: 2px solid #3d7a8c;
}
QHeaderView::section {
    background: #f0ebe3;
    color: #4a4540;
    border: none;
    padding: 6px;
}
QProgressBar {
    border: none;
    background: #ffffff;
    text-align: center;
    border-radius: 4px;
}
QProgressBar::chunk {
    background: #3d7a8c;
}
QStatusBar {
    background: #f0ebe3;
    color: #5c574f;
}
QSplitter::handle {
    background: transparent;
}
QFrame#card {
    background: #ffffff;
    border: none;
    border-radius: 6px;
}
QFrame#kpiCard {
    background: #ffffff;
    border: none;
    border-radius: 6px;
}
QWidget#dashboardStrip {
    background: transparent;
}
QWidget#sparkline, QWidget#multi-series-chart, QWidget#drawdown-chart,
QWidget#bar-chart, QWidget#scatter-chart, QWidget#equity-curve {
    background: transparent;
    border: none;
    border-radius: 6px;
}
QFrame#focusCard {
    background: #ffffff;
    border: none;
    border-radius: 8px;
}
QFrame#journalCard {
    background: #faf6ef;
    border: none;
    border-radius: 8px;
}
QListWidget#journalList {
    background: #faf6ef;
    border: none;
    border-radius: 8px;
}
QListWidget#journalList::item {
    color: #8a6d3b;
}
QListWidget#journalList::item:selected {
    background: #e0d5c4;
    color: #2c2825;
}
QFrame#pulseCard {
    background: #ffffff;
    border: none;
    border-radius: 8px;
}
QFrame#pulseCardItem {
    border: none;
    border-radius: 6px;
}
QFrame#learnCard {
    background: #ffffff;
    border: none;
    border-radius: 8px;
}
QFrame#terminalPanel {
    background: #ffffff;
    border: none;
    border-radius: 6px;
}
QFrame#terminalPanel:focus-within {
    background: #eef4f7;
}
QFrame#chatUser {
    background: #eef4f7;
    border-radius: 8px;
}
QFrame#chatNayak {
    background: #ffffff;
    border: none;
    border-radius: 8px;
}
QFrame#emptyState {
    background: #ffffff;
    border: none;
    border-radius: 8px;
}
QFrame#runningBanner {
    background: #e8f2fb;
    border: 1px solid #b8d4ef;
    border-radius: 6px;
}
QFrame#nayakTip {
    background: #eef4f7;
    border: none;
    border-radius: 8px;
}
QWidget#contextHost {
    background: #eef4f7;
    border: none;
    border-radius: 6px;
}
QLabel#navHeader {
    color: #8a8378;
    font-size: 11px;
    font-weight: 600;
    padding: 12px 16px 4px 16px;
}
QTabWidget::pane {
    border: none;
    border-radius: 6px;
}
QTabBar::tab {
    background: #f0ebe3;
    padding: 6px 12px;
    border: none;
}
QTabBar::tab:selected {
    background: #ffffff;
}
QPushButton:focus {
    outline: 2px solid #3d7a8c;
    outline-offset: 1px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus, QComboBox:focus {
    outline: 2px solid #3d7a8c;
    outline-offset: 0px;
}
QTableWidget:focus {
    outline: 2px solid #3d7a8c;
}
QListWidget#nav-list:focus {
    outline: 2px solid #3d7a8c;
}
QFrame#focusCard:focus-within {
    outline: 2px solid #3d7a8c;
    outline-offset: 0px;
}
QPlainTextEdit#log-view {
    font-family: "SF Mono", Menlo, Monaco, monospace;
    font-size: 12px;
    background: #ffffff;
    border: none;
}
"""

# Backward compatibility
STYLESHEET = DARK_STYLESHEET


def stylesheet_for(theme: UiTheme) -> str:
    return LIGHT_STYLESHEET if theme is UiTheme.LIGHT else DARK_STYLESHEET


def apply_theme(app: QApplication | None, theme: UiTheme) -> None:
    global _ACTIVE_UI_THEME
    _ACTIVE_UI_THEME = theme
    _set_chart_palette(theme)
    target = app or QApplication.instance()
    if isinstance(target, QApplication):
        target.setStyleSheet(stylesheet_for(theme))
