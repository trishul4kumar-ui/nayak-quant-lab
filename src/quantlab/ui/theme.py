"""Desktop visual language — dark and light themes."""

# ruff: noqa: E501

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
    background="#091725",
    muted="#7f9ab1",
    grid="#1b3b52",
    foreground="#eaf7ff",
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
            background="#091725",
            muted="#7f9ab1",
            grid="#1b3b52",
            foreground="#eaf7ff",
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

/* Shadow Operations glass system.  The translucent layers are intentionally
   restrained: research evidence and disabled-live state stay legible first. */
QMainWindow, QDialog, QWidget#mainRoot {
    background: #06111d;
}
QLabel {
    background: transparent;
}
QMenuBar {
    background: #081725;
    border-bottom: 1px solid rgba(112, 207, 255, 24);
    color: #b8d1e4;
}
QMenuBar::item:selected, QMenu::item:selected {
    background: rgba(20, 154, 212, 70);
}
QMenu {
    background: #0b1c2a;
    border: 1px solid rgba(112, 207, 255, 46);
    color: #eaf7ff;
}
QWidget#topBar {
    background: rgba(9, 27, 42, 232);
    border-bottom: 1px solid rgba(105, 209, 255, 42);
}
QLabel#brand {
    color: #dff7ff;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 1.5px;
}
QLabel#brandMeta, QLabel#sectionEyebrow {
    color: #57c9f6;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
}
QLabel#versionTag {
    color: #6f8ea6;
    font-family: "SF Mono", Menlo, Monaco, monospace;
    font-size: 11px;
}
QLineEdit#commandSearch {
    background: rgba(16, 44, 64, 196);
    border: 1px solid rgba(111, 208, 255, 58);
    border-radius: 9px;
    color: #eaf7ff;
    min-width: 300px;
    padding: 7px 12px;
}
QLineEdit#commandSearch:focus {
    border: 1px solid #43c7f4;
    outline: none;
}
QLabel#safetyRibbon {
    background: rgba(71, 49, 18, 235);
    border-bottom: 1px solid rgba(255, 190, 81, 105);
    color: #ffd78c;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .7px;
    padding: 7px 12px;
}
QWidget#navHost, QWidget#navHostLive {
    background: rgba(8, 25, 39, 224);
    border-right: 1px solid rgba(108, 201, 247, 34);
    padding: 8px 4px 8px 4px;
}
QWidget#navHostLive { background: rgba(61, 25, 29, 230); }
QListWidget, QListWidget#nav-list {
    background: transparent;
}
QListWidget#nav-list::item {
    color: #8faabd;
    border-left: 2px solid transparent;
    border-radius: 6px;
    margin: 1px 5px;
    padding: 7px 9px;
}
QListWidget#nav-list::item:hover {
    background: rgba(43, 128, 172, 47);
    color: #eaf7ff;
}
QListWidget#nav-list::item:selected {
    background: rgba(32, 139, 190, 82);
    border-left: 2px solid #4bd4ff;
    color: #f4fbff;
}
QLineEdit#navSearch {
    background: rgba(16, 44, 64, 176);
    border: 1px solid rgba(111, 208, 255, 44);
    border-radius: 7px;
    color: #eaf7ff;
}
QPushButton#navToggle {
    background: rgba(25, 69, 94, 160);
    color: #85dfff;
    border: 1px solid rgba(109, 210, 255, 45);
    border-radius: 6px;
}
QWidget#pageDeck, QScrollArea#pageScroll {
    background: #06111d;
}
QWidget#labShell, QWidget#homeWorkspace {
    background: transparent;
}
QLabel#pageTitle, QLabel#tkGreeting {
    color: #f1fbff;
    font-weight: 700;
}
QLabel#pageSubtitle, QLabel#nayakVoice, QLabel#chartLabel {
    color: #91aabd;
}
QFrame#card, QFrame#kpiCard, QFrame#focusCard, QFrame#pulseCard,
QFrame#journalCard, QFrame#terminalPanel, QFrame#nayakTip,
QFrame#emptyState, QFrame#learnCard, QFrame#runningBanner,
QWidget#contextHost, QFrame#notificationStrip {
    background: rgba(14, 37, 55, 216);
    border: 1px solid rgba(111, 208, 255, 34);
    border-radius: 10px;
}
QFrame#journalCard, QListWidget#journalList {
    background: rgba(17, 41, 58, 220);
}
QFrame#runningBanner {
    background: rgba(17, 52, 74, 230);
    border: 1px solid rgba(76, 198, 241, 88);
}
QLabel#contextStrip {
    background: transparent;
    color: #8bdfff;
    padding: 6px 8px;
}
QPushButton {
    background: rgba(31, 73, 97, 225);
    border: 1px solid rgba(122, 213, 255, 42);
    border-radius: 7px;
    color: #dceef7;
    font-weight: 600;
    padding: 7px 12px;
}
QPushButton:hover {
    background: rgba(43, 112, 147, 235);
    border-color: rgba(111, 218, 255, 112);
}
QPushButton#primary {
    background: #087fb1;
    border: 1px solid #43c7f4;
    color: #f5fcff;
}
QPushButton#primary:hover { background: #0998ce; }
QPushButton#modeToggle:checked {
    background: rgba(24, 127, 175, 235);
    border: 1px solid #4bd4ff;
    color: #f5fcff;
}
QLabel#modeBadge {
    background: rgba(15, 76, 102, 218);
    border: 1px solid rgba(86, 211, 255, 86);
    border-radius: 7px;
    color: #a9ebff;
}
QLabel#modeBadgeLive, QLabel#liveBanner {
    background: #7a292f;
    border: 1px solid #f0646c;
    border-radius: 7px;
    color: #ffecef;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QComboBox {
    background: rgba(11, 33, 49, 235);
    border: 1px solid rgba(111, 208, 255, 42);
    border-radius: 7px;
    color: #eaf7ff;
}
QTableWidget {
    background: rgba(8, 24, 37, 190);
    alternate-background-color: rgba(17, 44, 62, 144);
    selection-background-color: rgba(35, 139, 190, 105);
    color: #dcecf6;
    border: 1px solid rgba(111, 208, 255, 28);
    border-radius: 9px;
}
QHeaderView::section {
    background: rgba(19, 52, 72, 238);
    color: #93b8cc;
    border: none;
    border-bottom: 1px solid rgba(111, 208, 255, 34);
    padding: 8px;
    font-size: 11px;
    font-weight: 700;
}
QTabBar::tab {
    background: rgba(15, 43, 60, 196);
    border: 1px solid rgba(111, 208, 255, 28);
    border-radius: 6px;
    color: #8faabd;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background: rgba(27, 113, 153, 178);
    color: #f3fbff;
}
QStatusBar, QStatusBar QWidget#footerStatusHost {
    background: #071522;
    border-top: 1px solid rgba(111, 208, 255, 28);
    color: #86a4b6;
}
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: rgba(86, 140, 170, 110); border-radius: 5px; min-height: 28px; }
QScrollBar::handle:vertical:hover { background: #3aaed7; }
QSplitter::handle { background: rgba(48, 127, 166, 128); }
QSplitter::handle:hover { background: #44c9f4; }
QSplitter::handle:horizontal { width: 8px; margin: 4px 0; }
QSplitter::handle:vertical { height: 8px; margin: 0 4px; }
QPushButton#panelFocus { min-width: 58px; padding: 3px 7px; font-size: 11px; }
QPushButton#panelFocus:checked { background: rgba(41, 149, 198, 235); border-color: #4bd4ff; }
QPushButton:disabled { background: rgba(25, 45, 59, 190); border-color: rgba(111, 208, 255, 18); color: #5c7789; }
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

/* Light mode keeps the same control-plane hierarchy with frosted, high-contrast panels. */
QMainWindow, QDialog, QWidget#mainRoot, QWidget#pageDeck, QScrollArea#pageScroll {
    background: #edf5f9;
}
QLabel {
    background: transparent;
}
QMenuBar {
    background: #f5fbff;
    border-bottom: 1px solid rgba(37, 118, 156, 45);
}
QWidget#topBar {
    background: rgba(250, 254, 255, 240);
    border-bottom: 1px solid rgba(39, 132, 175, 54);
}
QLabel#brand { color: #07334a; font-weight: 700; }
QLabel#brandMeta, QLabel#sectionEyebrow { color: #087ba8; font-size: 10px; font-weight: 700; letter-spacing: 1.2px; }
QLabel#versionTag { color: #597688; font-family: "SF Mono", Menlo, Monaco, monospace; font-size: 11px; }
QLineEdit#commandSearch {
    background: rgba(237, 248, 253, 230);
    border: 1px solid rgba(29, 126, 170, 68);
    border-radius: 9px;
    min-width: 300px;
    padding: 7px 12px;
}
QLabel#safetyRibbon {
    background: rgba(255, 244, 215, 246);
    border-bottom: 1px solid rgba(177, 115, 0, 86);
    color: #805800;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .7px;
    padding: 7px 12px;
}
QWidget#navHost, QWidget#navHostLive {
    background: rgba(247, 252, 255, 228);
    border-right: 1px solid rgba(37, 118, 156, 42);
    padding: 8px 4px 8px 4px;
}
QWidget#navHostLive { background: rgba(255, 241, 241, 235); }
QListWidget, QListWidget#nav-list { background: transparent; }
QListWidget#nav-list::item { border-left: 2px solid transparent; border-radius: 6px; margin: 1px 5px; padding: 7px 9px; }
QListWidget#nav-list::item:hover { background: rgba(47, 151, 196, 30); }
QListWidget#nav-list::item:selected { background: rgba(34, 145, 195, 68); border-left: 2px solid #078fcb; }
QLineEdit#navSearch { background: rgba(236, 248, 254, 220); border: 1px solid rgba(37, 126, 170, 48); border-radius: 7px; }
QWidget#labShell, QWidget#homeWorkspace { background: transparent; }
QLabel#pageTitle, QLabel#tkGreeting { color: #082e43; font-weight: 700; }
QLabel#pageSubtitle, QLabel#nayakVoice, QLabel#chartLabel { color: #526d7c; }
QFrame#card, QFrame#kpiCard, QFrame#focusCard, QFrame#pulseCard,
QFrame#journalCard, QFrame#terminalPanel, QFrame#nayakTip,
QFrame#emptyState, QFrame#learnCard, QFrame#runningBanner,
QWidget#contextHost, QFrame#notificationStrip {
    background: rgba(255, 255, 255, 222);
    border: 1px solid rgba(37, 118, 156, 40);
    border-radius: 10px;
}
QFrame#journalCard, QListWidget#journalList { background: rgba(248, 253, 255, 232); }
QPushButton { background: rgba(231, 244, 250, 235); border: 1px solid rgba(37, 126, 170, 48); border-radius: 7px; color: #16435a; font-weight: 600; padding: 7px 12px; }
QPushButton:hover { background: rgba(205, 235, 247, 245); border-color: rgba(23, 139, 190, 104); }
QPushButton#primary { background: #087fab; border: 1px solid #087fab; color: #ffffff; }
QPushButton#primary:hover { background: #0694c7; }
QPushButton#modeToggle:checked { background: rgba(30, 141, 191, 120); border: 1px solid #087fab; }
QLabel#modeBadge { background: rgba(217, 242, 251, 238); border: 1px solid rgba(20, 135, 183, 72); border-radius: 7px; color: #075274; }
QLabel#modeBadgeLive, QLabel#liveBanner { background: #a43a43; border: 1px solid #c9545d; border-radius: 7px; color: #fff6f6; }
QTableWidget { background: rgba(255, 255, 255, 205); alternate-background-color: rgba(232, 246, 252, 160); selection-background-color: rgba(69, 172, 214, 100); border: 1px solid rgba(37, 118, 156, 34); border-radius: 9px; }
QHeaderView::section { background: rgba(229, 245, 252, 240); color: #4b7286; border: none; border-bottom: 1px solid rgba(37, 118, 156, 36); padding: 8px; font-size: 11px; font-weight: 700; }
QTabBar::tab { background: rgba(231, 245, 251, 220); border: 1px solid rgba(37, 118, 156, 32); border-radius: 6px; margin-right: 4px; }
QTabBar::tab:selected { background: rgba(137, 213, 241, 154); color: #063a55; }
QStatusBar, QStatusBar QWidget#footerStatusHost { background: #f4fbff; border-top: 1px solid rgba(37, 118, 156, 30); }
QSplitter::handle { background: rgba(72, 153, 190, 105); }
QSplitter::handle:hover { background: #0a96c8; }
QSplitter::handle:horizontal { width: 8px; margin: 4px 0; }
QSplitter::handle:vertical { height: 8px; margin: 0 4px; }
QPushButton#panelFocus { min-width: 58px; padding: 3px 7px; font-size: 11px; }
QPushButton#panelFocus:checked { background: rgba(84, 187, 222, 150); border-color: #087fab; }
QPushButton:disabled { background: rgba(225, 235, 240, 180); border-color: rgba(37, 118, 156, 20); color: #8399a5; }
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
