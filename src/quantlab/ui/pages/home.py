from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from quantlab.app.assistant import FocusAction, NayakAssistant
from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.chart_data import latest_equity, latest_run_metrics
from quantlab.app.copy import SYNTHETIC_SHARPE_DISCLAIMER
from quantlab.app.settings_store import ExperienceMode
from quantlab.ui.widgets.charts import DashboardStrip, SparklineWidget
from quantlab.ui.widgets.lab_shell import data_kind_badge
from quantlab.ui.widgets.pulse_panel import PulsePanel
from quantlab.ui.widgets.research_pipeline import ResearchPipelineStrip


class HomePage(QWidget):
    def __init__(
        self,
        runtime: ApplicationRuntime,
        *,
        on_action: Callable[[FocusAction], None],
        on_journal: Callable[[str], None] | None = None,
        on_nav: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("homeWorkspace")
        self._runtime = runtime
        self._assistant = NayakAssistant(runtime)
        self._on_action = on_action
        self._on_journal = on_journal
        self._on_nav = on_nav

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        self._greeting = QLabel()
        self._greeting.setObjectName("tkGreeting")
        self._status = QLabel()
        self._status.setObjectName("nayakVoice")
        self._status.setWordWrap(True)

        root.addWidget(self._greeting)
        root.addWidget(self._status)

        self._nudge_row = QHBoxLayout()
        self._nudges = QLabel()
        self._nudges.setObjectName("contextStrip")
        self._nudges.setWordWrap(True)
        self._nudge_action = QPushButton()
        self._nudge_action.setVisible(False)
        self._nudge_action.clicked.connect(self._run_nudge_action)
        self._nudge_row.addWidget(self._nudges, 1)
        self._nudge_row.addWidget(self._nudge_action)
        root.addLayout(self._nudge_row)

        pipe_label = QLabel("RESEARCH CONTROL PLANE")
        pipe_label.setObjectName("sectionEyebrow")
        root.addWidget(pipe_label)
        self._pipeline = ResearchPipelineStrip(on_nav=self._on_nav)
        root.addWidget(self._pipeline)

        self._intent_frame = QFrame()
        self._intent_frame.setObjectName("focusCard")
        intent_layout = QVBoxLayout(self._intent_frame)
        intent_layout.setContentsMargins(20, 16, 20, 16)
        intent_head = QLabel("What brings you here today?")
        intent_head.setStyleSheet("font-size: 16px; font-weight: 600;")
        intent_sub = QLabel("Pick a path — you can change anytime from the sidebar or ⌘K.")
        intent_sub.setWordWrap(True)
        intent_sub.setObjectName("nayakVoice")
        intent_layout.addWidget(intent_head)
        intent_layout.addWidget(intent_sub)
        intent_row = QHBoxLayout()
        for label, intent_key in (
            ("Test an idea", "test"),
            ("Learn the workflow", "learn"),
            ("Explore Full Lab", "full"),
        ):
            btn = QPushButton(label)
            btn.setObjectName("primary" if intent_key == "test" else "")
            btn.clicked.connect(lambda checked=False, key=intent_key: self._pick_intent(key))
            intent_row.addWidget(btn)
        intent_layout.addLayout(intent_row)
        root.addWidget(self._intent_frame)

        self._focus_frame = QFrame()
        self._focus_frame.setObjectName("focusCard")
        focus_layout = QVBoxLayout(self._focus_frame)
        focus_layout.setContentsMargins(20, 16, 20, 16)
        self._nayak_label = QLabel("NAYAK SAYS")
        self._nayak_label.setObjectName("nayakLabel")
        self._focus_title = QLabel()
        self._focus_title.setStyleSheet("font-size: 16px; font-weight: 600;")
        self._focus_body = QLabel()
        self._focus_body.setWordWrap(True)
        self._focus_body.setStyleSheet("color: #b4b8c2;")
        self._focus_step = QLabel()
        self._focus_step.setStyleSheet("color: #6b7080; font-size: 12px;")
        self._focus_btn = QPushButton()
        self._focus_btn.setObjectName("primary")
        self._focus_btn.clicked.connect(self._run_focus_action)
        self._current_action = FocusAction.ONBOARDING

        focus_layout.addWidget(self._nayak_label)
        focus_layout.addWidget(self._focus_step)
        focus_layout.addWidget(self._focus_title)
        focus_layout.addWidget(self._focus_body)
        focus_layout.addWidget(self._focus_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        root.addWidget(self._focus_frame)

        dash_title = QLabel("TELEMETRY SNAPSHOT")
        dash_title.setObjectName("sectionEyebrow")
        dash_row = QHBoxLayout()
        dash_row.addWidget(dash_title)
        self._data_kind_host = QHBoxLayout()
        dash_row.addLayout(self._data_kind_host)
        dash_row.addStretch()
        root.addLayout(dash_row)
        self._dash = DashboardStrip(["Sharpe", "Return", "Max DD", "Gate"])
        root.addWidget(self._dash)

        curve_row = QHBoxLayout()
        curve_col = QVBoxLayout()
        curve_label = QLabel("Latest equity curve")
        curve_label.setObjectName("chartLabel")
        self._equity_spark = SparklineWidget(min_height=100)
        self._equity_spark.set_empty_message("Run a backtest — your equity curve appears here")
        curve_col.addWidget(curve_label)
        curve_col.addWidget(self._equity_spark)
        curve_row.addLayout(curve_col, 1)
        root.addLayout(curve_row)

        self._lower_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._lower_splitter.setObjectName("homeWorkspaceSplitter")
        self._lower_splitter.setChildrenCollapsible(False)
        self._lower_splitter.setHandleWidth(8)
        self._lower_splitter.setOpaqueResize(True)
        journal_header = QHBoxLayout()
        journal_title = QLabel("EVIDENCE JOURNAL")
        journal_title.setObjectName("sectionEyebrow")
        journal_header.addWidget(journal_title)
        journal_header.addStretch()
        self._journal_open = QPushButton("Open journal →")
        self._journal_open.clicked.connect(lambda: self._on_nav and self._on_nav("journal"))
        journal_header.addWidget(self._journal_open)
        self._journal_list = QListWidget()
        self._journal_list.setObjectName("journalList")
        self._journal_list.itemClicked.connect(self._on_journal_clicked)
        journal_frame = QFrame()
        journal_frame.setObjectName("journalCard")
        journal_inner = QVBoxLayout(journal_frame)
        journal_inner.setContentsMargins(16, 16, 16, 16)
        journal_inner.addLayout(journal_header)
        journal_inner.addWidget(self._journal_list)
        self._pulse = PulsePanel(on_nav=self._on_nav)
        self._lower_splitter.addWidget(journal_frame)
        self._lower_splitter.addWidget(self._pulse)
        self._lower_splitter.handle(1).setToolTip("Drag to resize journal and system pulse")
        home_layout = runtime.ui_settings.current.terminal_layouts.get("workspace:home", {})
        sizes = home_layout.get("lower")
        if sizes and len(sizes) == self._lower_splitter.count():
            self._lower_splitter.setSizes(sizes)
        else:
            self._lower_splitter.setSizes([3, 2])
        self._lower_splitter.splitterMoved.connect(self._persist_lower_layout)
        root.addWidget(self._lower_splitter, 1)

        self._synthetic_note = QLabel(SYNTHETIC_SHARPE_DISCLAIMER)
        self._synthetic_note.setObjectName("nayakVoice")
        self._synthetic_note.setWordWrap(True)
        root.addWidget(self._synthetic_note)
        root.addStretch()
        self.refresh()

    def _persist_lower_layout(self, *_args: object) -> None:
        layouts = self._runtime.ui_settings.current.terminal_layouts
        payload = dict(layouts.get("workspace:home", {}))
        payload["lower"] = self._lower_splitter.sizes()
        layouts["workspace:home"] = payload
        self._runtime.ui_settings.save()

    def _set_data_kind_badge(self, data_kind: str | None) -> None:
        while self._data_kind_host.count():
            item = self._data_kind_host.takeAt(0)
            if item is None:
                break
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if data_kind:
            self._data_kind_host.addWidget(data_kind_badge(data_kind))

    def _pick_intent(self, intent: str) -> None:
        prefs = self._runtime.ui_settings.current
        prefs.onboarding_intent = intent
        self._runtime.ui_settings.save()
        self._intent_frame.setVisible(False)
        if self._on_nav is None:
            return
        if intent == "test":
            self._on_nav("test")
        elif intent == "learn":
            self._on_nav("learn")
        elif intent == "full":
            self._on_action(FocusAction.FULL_LAB)

    def _run_nudge_action(self) -> None:
        nudge = self._assistant.primary_context_nudge()
        if nudge is None or nudge.nav_key is None or self._on_nav is None:
            return
        self._on_nav(nudge.nav_key)

    def _on_journal_clicked(self, item: QListWidgetItem) -> None:
        exp_id = item.data(Qt.ItemDataRole.UserRole)
        if exp_id and self._on_journal is not None:
            self._on_journal(str(exp_id))

    def _run_focus_action(self) -> None:
        if self._current_action is FocusAction.ONBOARDING:
            self._assistant.complete_onboarding()
            self.refresh()
            return
        self._on_action(self._current_action)

    def refresh(self) -> None:
        guided = self._runtime.ui_settings.current.experience_mode is ExperienceMode.GUIDED
        self._focus_frame.setVisible(guided)

        self._greeting.setText(self._assistant.greeting())
        self._status.setText(self._assistant.status_line())

        nudge = self._assistant.primary_context_nudge()
        if nudge is None:
            self._nudges.setVisible(False)
            self._nudge_action.setVisible(False)
        else:
            self._nudges.setText(nudge.text)
            self._nudges.setVisible(True)
            if nudge.nav_key and nudge.action_label and self._on_nav is not None:
                self._nudge_action.setText(f"{nudge.action_label} →")
                self._nudge_action.setVisible(True)
            else:
                self._nudge_action.setVisible(False)

        if guided:
            focus = self._assistant.focus()
            self._current_action = focus.action
            self._focus_step.setText(f"Step {focus.step} of {focus.total_steps}")
            self._focus_title.setText(focus.title)
            self._focus_body.setText(focus.body)
            self._focus_btn.setText(f"{focus.action_label} →")

        groups = self._assistant.journal_groups()
        self._journal_list.clear()
        if not groups:
            empty_msg = (
                "No experiments yet — run Test from the focus card."
                if guided
                else "No experiments yet — run a backtest from Backtest Lab."
            )
            self._journal_list.addItem(empty_msg)
            self._journal_open.setEnabled(False)
        else:
            self._journal_open.setEnabled(True)
            for group in groups:
                count_suffix = f"  ×{group.count}" if group.count > 1 else ""
                time_suffix = f" · {group.run_at}" if group.run_at else ""
                label = f"{group.name}{count_suffix}{time_suffix}\n  {group.summary}"
                if group.note:
                    snippet = group.note[:50] + ("…" if len(group.note) > 50 else "")
                    label += f'\n  Note: "{snippet}"'
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, group.latest_id)
                self._journal_list.addItem(item)

        self._pulse.refresh(self._runtime)
        self._pipeline.refresh(self._runtime)

        milestones = set(self._runtime.ui_settings.current.milestones)
        prefs = self._runtime.ui_settings.current
        show_intent = "onboarding_complete" in milestones and not prefs.onboarding_intent
        self._intent_frame.setVisible(show_intent)

        metrics = latest_run_metrics(self._runtime)
        if metrics is None:
            self._set_data_kind_badge(None)
            for card in self._dash.cards:
                card.set_value("—")
                card.clear_target_progress()
            self._equity_spark.set_values([])
            return
        data_kind = str(metrics.get("data_kind") or "synthetic")
        self._set_data_kind_badge(data_kind)
        sharpe = metrics.get("sharpe")
        ret = metrics.get("total_return")
        dd = metrics.get("max_drawdown")
        gate = metrics.get("gate_outcome") or "—"
        sharpe_f = sharpe if isinstance(sharpe, float) else None
        dd_f = dd if isinstance(dd, float) else None
        self._dash.card(0).set_value(
            f"{sharpe_f:.2f}" if sharpe_f is not None else "—",
            accent="#42a5f5",
        )
        if sharpe_f is not None:
            self._dash.card(0).set_target_progress(
                sharpe_f,
                1.0,
                headroom_label=f"{'Above' if sharpe_f >= 1.0 else 'Below'} 1.0 Sharpe target",
            )
        else:
            self._dash.card(0).clear_target_progress()

        self._dash.card(1).set_value(
            f"{ret:.1%}" if isinstance(ret, float) else "—",
            accent="#66bb6a" if isinstance(ret, float) and ret >= 0 else "#ef5350",
        )
        self._dash.card(1).clear_target_progress()

        self._dash.card(2).set_value(
            f"{dd_f:.1%}" if dd_f is not None else "—",
            accent="#ef5350",
        )
        if dd_f is not None:
            limit = 0.15
            headroom = max(limit - abs(dd_f), 0.0)
            self._dash.card(2).set_target_progress(
                abs(dd_f),
                limit,
                higher_is_better=False,
                headroom_label=f"Room to {limit:.0%} limit: {headroom:.1%}",
            )
        else:
            self._dash.card(2).clear_target_progress()

        gate_color = "#66bb6a" if str(gate).lower() == "pass" else "#ffa726"
        self._dash.card(3).set_value(str(gate)[:12], accent=gate_color)
        self._dash.card(3).set_subtitle(
            "All checks pass" if str(gate).lower() == "pass" else "Review validation"
        )

        latest = latest_equity(self._runtime)
        if latest:
            _, curve = latest
            self._equity_spark.set_values(curve)
            self._dash.card(1).set_sparkline(curve, color="#66bb6a")
        else:
            self._equity_spark.set_values([])

    def refresh_pulse(self) -> None:
        """Lightweight pulse-only update (e.g. on timer tick)."""
        self._pulse.refresh(self._runtime)
