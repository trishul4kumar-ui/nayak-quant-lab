from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from quantlab.app.assistant import NayakAssistant
from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.health import ComponentStatus
from quantlab.app.settings_store import ExperienceMode
from quantlab.ui.widgets import fill_table


class WelcomeDialog(QDialog):
    """First-launch welcome for TK — replaces the bare health splash."""

    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__()
        self._runtime = runtime
        self._assistant = NayakAssistant(runtime)
        self.setWindowTitle("Welcome to NAYAK QUANT LAB")
        self.setModal(True)
        self.resize(620, 480)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._page_intro())
        self._stack.addWidget(self._page_safety())
        self._stack.addWidget(self._page_mode())
        self._stack.addWidget(self._page_tour())

        self._back = QPushButton("Back")
        self._next = QPushButton("Next")
        self._next.setObjectName("primary")
        self._back.clicked.connect(self._go_back)
        self._next.clicked.connect(self._go_next)

        nav = QHBoxLayout()
        nav.addWidget(self._back)
        nav.addStretch()
        nav.addWidget(self._next)

        root = QVBoxLayout(self)
        root.addWidget(self._stack)
        root.addLayout(nav)
        self._update_nav()

    def _page_intro(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        greeting = QLabel(self._assistant.greeting())
        greeting.setObjectName("tkGreeting")
        nayak = QLabel("NAYAK SAYS")
        nayak.setObjectName("nayakLabel")
        body = QLabel(
            f"I'm your quantitative research assistant, {self._assistant.tk_name}.\n\n"
            "This is your private lab for testing trading ideas on data — "
            "momentum, validation, portfolio construction — before any real money.\n\n"
            "Nothing in this app places live NSE orders unless every safety gate passes "
            "(and that is off by default)."
        )
        body.setWordWrap(True)
        body.setObjectName("nayakVoice")
        layout.addWidget(greeting)
        layout.addWidget(nayak)
        layout.addWidget(body)
        layout.addStretch()
        return page

    def _page_safety(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("Research-only by default")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        body = QLabel(
            "Mode: RESEARCH\n"
            "Live trading: DISABLED\n"
            "Broker: DISCONNECTED\n\n"
            "We use synthetic NSE-style data to learn safely. "
            "A good Sharpe on synthetic drift is practice — not proof of real alpha."
        )
        body.setWordWrap(True)
        body.setStyleSheet("color: #b4b8c2;")
        table = QTableWidget()
        rows = []
        for component in self._runtime.health.components:
            mark = {
                ComponentStatus.OK: "OK",
                ComponentStatus.OPTIONAL: "OPTIONAL",
                ComponentStatus.FAILED: "FAILED",
            }[component.status]
            rows.append([component.name, mark, component.detail])
        fill_table(table, ["Component", "Status", "Detail"], rows)
        layout.addWidget(title)
        layout.addWidget(body)
        layout.addWidget(table)
        return page

    def _page_mode(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("How do you want to start?")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        hint = QLabel("You can switch anytime with the Guided / Full Lab toggle in the header.")
        hint.setWordWrap(True)
        hint.setObjectName("nayakVoice")

        self._guided_radio = QRadioButton(
            "Guided Lab — Home, Learn, Test wizard, Journal (recommended)"
        )
        self._full_radio = QRadioButton("Full Lab — full terminal, all modules immediately")
        self._guided_radio.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self._guided_radio)
        group.addButton(self._full_radio)

        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self._guided_radio)
        layout.addWidget(self._full_radio)
        layout.addStretch()
        return page

    def _page_tour(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("Your lab in 60 seconds")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        tour = QLabel(
            "1. Home — I greet you and suggest one next step.\n"
            "2. Test — 3-step wizard for your first momentum experiment.\n"
            "3. Journal — your notebook; save notes on each run.\n"
            "4. Learn — concepts unlock as you progress.\n"
            "5. Full Lab — terminal panels when you are ready."
        )
        tour.setWordWrap(True)
        tour.setStyleSheet("color: #c9a96e; line-height: 1.5;")
        layout.addWidget(title)
        layout.addWidget(tour)
        layout.addStretch()
        return page

    def _go_back(self) -> None:
        idx = self._stack.currentIndex()
        if idx > 0:
            self._stack.setCurrentIndex(idx - 1)
            self._update_nav()

    def _go_next(self) -> None:
        idx = self._stack.currentIndex()
        if idx < self._stack.count() - 1:
            self._stack.setCurrentIndex(idx + 1)
            self._update_nav()
            return
        self._finish()

    def _update_nav(self) -> None:
        idx = self._stack.currentIndex()
        self._back.setEnabled(idx > 0)
        self._next.setText("Enter the lab →" if idx == self._stack.count() - 1 else "Next")

    def _finish(self) -> None:
        prefs = self._runtime.ui_settings.current
        prefs.experience_mode = (
            ExperienceMode.FULL if self._full_radio.isChecked() else ExperienceMode.GUIDED
        )
        if prefs.experience_mode is ExperienceMode.FULL:
            self._assistant.record_milestone("full_lab_unlocked")
        self._assistant.complete_onboarding()
        self._runtime.ui_settings.save()
        self.accept()
