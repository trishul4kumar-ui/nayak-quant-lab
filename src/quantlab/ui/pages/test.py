from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from quantlab.app.assistant import NayakAssistant
from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.copy import SYNTHETIC_SHARPE_DISCLAIMER
from quantlab.app.jobs import Job, JobStatus
from quantlab.app.strategy_templates import TEMPLATES, template_by_id
from quantlab.ui.widgets import EquityCurveWidget, ExplainChip, fill_table
from quantlab.ui.widgets.charts import DashboardStrip
from quantlab.ui.widgets.lab_shell import LabPageShell, data_kind_badge


class BacktestWizardPage(LabPageShell):
    """3-step guided backtest wizard for TK."""

    def __init__(
        self,
        runtime: ApplicationRuntime,
        *,
        on_done: Callable[[], None],
        on_journal: Callable[[str], None] | None = None,
        on_compare: Callable[[], None] | None = None,
        on_validation: Callable[[], None] | None = None,
        on_full_lab: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(
            "Test wizard",
            subtitle="Four-step guided backtest — pick a template, run, read results.",
            nayak_summary=(
                "Hypothesis: higher 20-day momentum predicts next-bar return after costs. "
                "Fills are next-bar only — no look-ahead."
            ),
        )
        self._runtime = runtime
        self._assistant = NayakAssistant(runtime)
        self._on_done = on_done
        self._on_journal = on_journal
        self._on_compare = on_compare
        self._on_validation = on_validation
        self._on_full_lab = on_full_lab
        self._job: Job | None = None
        self._last_experiment_id: str = ""

        self._step_label = QLabel("Step 1 of 4")
        self._step_label.setStyleSheet("color: #6b7080;")
        self.add_toolbar_widget(self._step_label)

        body = self.body()
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_step_template())
        self._stack.addWidget(self._build_step_what())
        self._stack.addWidget(self._build_step_run())
        self._stack.addWidget(self._build_step_result())
        body.addWidget(self._stack, 1)

        nav = QHBoxLayout()
        self._back = QPushButton("Back")
        self._back.clicked.connect(self._go_back)
        self._next = QPushButton("Next")
        self._next.setObjectName("primary")
        self._next.clicked.connect(self._go_next)
        nav.addWidget(self._back)
        nav.addStretch()
        nav.addWidget(self._next)
        body.addLayout(nav)
        template = template_by_id(self._runtime.ui_settings.current.selected_template)
        self._hypothesis_body.setText(
            f"{self._assistant.tk_name}, testing: {template.name}\n\n"
            f"Hypothesis: {template.hypothesis}\n\n"
            "Fills: next bar only (no look-ahead)."
        )
        self._update_nav()

    def _build_step_template(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        head = QLabel("Pick a strategy template")
        head.setStyleSheet("font-weight: 600; font-size: 15px;")
        layout.addWidget(head)
        self._template_group = QButtonGroup(page)
        prefs = self._runtime.ui_settings.current
        selected = prefs.selected_template or TEMPLATES[0].template_id
        for template in TEMPLATES:
            frame = QFrame()
            frame.setObjectName("card")
            row = QVBoxLayout(frame)
            row.setContentsMargins(12, 10, 12, 10)
            radio = QRadioButton(template.name)
            radio.setChecked(template.template_id == selected)
            self._template_group.addButton(radio)
            radio.setProperty("template_id", template.template_id)
            summary = QLabel(template.summary)
            summary.setWordWrap(True)
            summary.setObjectName("nayakVoice")
            if not template.runnable:
                badge = QLabel("Preview — runs momentum engine in this build")
                badge.setStyleSheet("color: #ffb74d; font-size: 11px;")
                row.addWidget(badge)
            row.addWidget(radio)
            row.addWidget(summary)
            layout.addWidget(frame)
        layout.addStretch()
        return page

    def _selected_template(self):
        for button in self._template_group.buttons():
            if button.isChecked():
                tid = button.property("template_id")
                return template_by_id(str(tid))
        return template_by_id(self._runtime.ui_settings.current.selected_template)

    def _build_step_what(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        nayak = QLabel("NAYAK SAYS")
        nayak.setObjectName("nayakLabel")
        self._hypothesis_body = QLabel()
        self._hypothesis_body.setWordWrap(True)
        self._hypothesis_body.setStyleSheet("color: #b4b8c2;")
        layout.addWidget(nayak)
        layout.addWidget(self._hypothesis_body)
        layout.addWidget(ExplainChip("momentum_20", label="Momentum"))
        layout.addWidget(ExplainChip("cost_bps", label="Costs"))
        layout.addStretch()
        return page

    def _build_step_run(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self._run_status = QLabel("Ready to run.")
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._run_btn = QPushButton("Run momentum backtest")
        self._run_btn.setObjectName("primary")
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setEnabled(False)
        self._run_btn.clicked.connect(self._start_job)
        self._cancel_btn.clicked.connect(self._cancel_job)
        row = QHBoxLayout()
        row.addWidget(self._run_btn)
        row.addWidget(self._cancel_btn)
        layout.addWidget(self._run_status)
        layout.addWidget(self._progress)
        layout.addLayout(row)
        layout.addStretch()
        return page

    def _build_step_result(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self._result_intro = QLabel()
        self._result_intro.setWordWrap(True)
        self._result_intro.setObjectName("nayakVoice")
        self._result_badge_row = QHBoxLayout()
        self._result_badge_host = QHBoxLayout()
        self._result_badge_row.addLayout(self._result_badge_host)
        self._result_badge_row.addStretch()
        self._dash = DashboardStrip(["Sharpe", "Return", "Max DD", "Gate"])
        self._curve = EquityCurveWidget()
        self._metrics = QTableWidget()
        layout.addWidget(self._result_intro)
        layout.addLayout(self._result_badge_row)
        layout.addWidget(self._dash)
        layout.addWidget(ExplainChip("sharpe", label="Equity curve"))
        layout.addWidget(self._curve, 1)
        layout.addWidget(self._metrics)

        note_title = QLabel("Quick journal note")
        note_title.setStyleSheet("font-weight: 600;")
        self._quick_note = QPlainTextEdit()
        self._quick_note.setPlaceholderText("What did you observe? One line is enough.")
        self._quick_note.setMaximumHeight(80)
        save_row = QHBoxLayout()
        self._save_note_btn = QPushButton("Save note")
        self._save_note_btn.clicked.connect(self._save_quick_note)
        self._note_saved = QLabel()
        self._note_saved.setObjectName("nayakVoice")
        save_row.addWidget(self._save_note_btn)
        save_row.addWidget(self._note_saved)
        save_row.addStretch()
        layout.addWidget(note_title)
        layout.addWidget(self._quick_note)
        layout.addLayout(save_row)

        handoff = QHBoxLayout()
        self._compare_btn = QPushButton("Compare in Full Lab →")
        self._validate_btn = QPushButton("Run validation →")
        self._full_lab_btn = QPushButton("Open Full Lab →")
        self._compare_btn.clicked.connect(self._go_compare)
        self._validate_btn.clicked.connect(self._go_validation)
        self._full_lab_btn.clicked.connect(self._go_full_lab)
        handoff.addWidget(self._compare_btn)
        handoff.addWidget(self._validate_btn)
        handoff.addWidget(self._full_lab_btn)
        handoff.addStretch()
        layout.addLayout(handoff)
        return page

    def poll(self) -> None:
        if self._job is None:
            return
        job = self._runtime.jobs.get(self._job.job_id)
        if job is None:
            return
        self._progress.setValue(int(job.progress * 100))
        self._run_status.setText(f"{job.status.value}  {job.progress:.0%}")
        if job.status in {JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.CANCELLING}:
            self.set_running(f"Backtest {job.status.value} — {job.progress:.0%}")
        else:
            self.set_running(None)
        if job.status is JobStatus.COMPLETED:
            self.set_running(None)
            self._job = None
            self._run_btn.setEnabled(True)
            self._cancel_btn.setEnabled(False)
            self._show_result(job)
            self._stack.setCurrentIndex(3)
            self._update_nav()
            self._runtime.record_notification("Backtest completed")
            self._on_done()
        elif job.status in {JobStatus.FAILED, JobStatus.CANCELLED}:
            self.set_running(None)
            self._run_status.setText(f"{job.status.value}: {job.error or ''}")
            self._job = None
            self._run_btn.setEnabled(True)
            self._cancel_btn.setEnabled(False)

    def open_at_run_step(self) -> None:
        self._stack.setCurrentIndex(2)
        self._update_nav()

    def reset_wizard(self) -> None:
        self._stack.setCurrentIndex(0)
        self._job = None
        self._run_status.setText("Ready to run.")
        self._progress.setValue(0)
        self._quick_note.clear()
        self._note_saved.clear()
        self._update_nav()

    def _start_job(self) -> None:
        template = self._selected_template()
        prefs = self._runtime.ui_settings.current
        prefs.selected_template = template.template_id
        prefs.last_n_days = template.n_days
        prefs.last_lookback = template.lookback
        prefs.last_top_n = template.top_n
        prefs.last_cost_bps = template.cost_bps
        self._runtime.ui_settings.save()
        if not template.runnable:
            self._run_status.setText("Template preview — running default momentum engine.")
        self._job = self._runtime.submit_momentum_backtest(
            {
                "n_days": template.n_days,
                "lookback": template.lookback,
                "top_n": template.top_n,
                "cost_bps": template.cost_bps,
            }
        )
        self._run_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._run_status.setText(f"Queued {self._job.job_id[:8]}")

    def _cancel_job(self) -> None:
        if self._job is not None:
            self._runtime.jobs.cancel(self._job.job_id)

    def _clear_result_badge(self) -> None:
        while self._result_badge_host.count():
            item = self._result_badge_host.takeAt(0)
            if item is None:
                break
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _set_result_badge(self, data_kind: str) -> None:
        self._clear_result_badge()
        self._result_badge_host.addWidget(data_kind_badge(data_kind))

    def _show_result(self, job: Job) -> None:
        result = job.result or {}
        equity = [float(x) for x in result.get("equity_curve", [])]
        self._curve.set_values(equity)
        metrics = result.get("metrics") or {}
        sharpe = metrics.get("sharpe")
        ret = metrics.get("total_return")
        dd = metrics.get("max_drawdown")
        gate = metrics.get("gate_outcome") or result.get("gate_outcome") or "—"
        data_kind = str(result.get("data_kind") or metrics.get("data_kind") or "synthetic")
        sharpe_txt = f"{sharpe:.2f}" if isinstance(sharpe, float) else "n/a"
        exp_id = str(result.get("experiment_id", ""))
        self._last_experiment_id = exp_id
        prefs = self._runtime.ui_settings.current
        existing = prefs.journal_notes.get(exp_id, "")
        self._quick_note.setPlainText(existing)
        self._note_saved.clear()
        self._set_result_badge(data_kind)
        self._dash.card(0).set_value(
            sharpe_txt,
            accent="#42a5f5",
        )
        if isinstance(sharpe, float):
            self._dash.card(0).set_target_progress(sharpe, 1.0, headroom_label="vs 1.0 Sharpe target")
        if isinstance(dd, float):
            self._dash.card(2).set_target_progress(
                abs(dd),
                0.15,
                higher_is_better=False,
                headroom_label=f"Room to 15% limit: {max(0.15 - abs(dd), 0):.1%}",
            )
        self._dash.card(1).set_value(
            f"{ret:.1%}" if isinstance(ret, float) else "—",
            accent="#66bb6a" if isinstance(ret, float) and ret >= 0 else "#ef5350",
        )
        self._dash.card(2).set_value(
            f"{dd:.1%}" if isinstance(dd, float) else "—",
            accent="#ef5350",
        )
        gate_color = "#66bb6a" if str(gate).lower() == "pass" else "#ffa726"
        self._dash.card(3).set_value(str(gate)[:12], accent=gate_color)
        self._result_intro.setText(
            f"Done, {self._assistant.tk_name}. Sharpe {sharpe_txt}. "
            f"{SYNTHETIC_SHARPE_DISCLAIMER}"
        )
        rows = [[k, f"{v:.4f}" if isinstance(v, float) else str(v)] for k, v in metrics.items()]
        rows.insert(0, ["experiment_id", exp_id[:12]])
        rows.insert(1, ["data_kind", data_kind])
        fill_table(self._metrics, ["Metric", "Value"], rows, experiment_links={(0, 1): exp_id})

    def _go_compare(self) -> None:
        if self._on_compare is not None:
            self._on_compare()

    def _go_validation(self) -> None:
        if self._on_validation is not None:
            self._on_validation()

    def _go_full_lab(self) -> None:
        if self._on_full_lab is not None:
            self._on_full_lab()

    def _save_quick_note(self) -> bool:
        if not self._last_experiment_id:
            return False
        saved = self._assistant.save_journal_note(
            self._last_experiment_id,
            self._quick_note.toPlainText(),
        )
        if saved:
            self._note_saved.setText("Saved to your lab journal.")
        return saved

    def _go_back(self) -> None:
        idx = self._stack.currentIndex()
        if idx == 2 and self._job is not None:
            return
        if idx > 0:
            self._stack.setCurrentIndex(idx - 1)
            self._update_nav()

    def _go_next(self) -> None:
        idx = self._stack.currentIndex()
        if idx == 0:
            template = self._selected_template()
            prefs = self._runtime.ui_settings.current
            prefs.selected_template = template.template_id
            self._runtime.ui_settings.save()
            self._hypothesis_body.setText(
                f"{self._assistant.tk_name}, testing: {template.name}\n\n"
                f"Hypothesis: {template.hypothesis}\n\n"
                "Fills: next bar only (no look-ahead)."
            )
            self._stack.setCurrentIndex(1)
            self._update_nav()
            return
        if idx == 1:
            self._stack.setCurrentIndex(2)
            self._update_nav()
            return
        if idx == 2:
            if self._job is None:
                self._start_job()
            return
        if idx == 3:
            self._save_quick_note()
            if self._on_journal and self._last_experiment_id:
                self._on_journal(self._last_experiment_id)

    def _update_nav(self) -> None:
        idx = self._stack.currentIndex()
        self._step_label.setText(f"Step {idx + 1} of 4")
        self._back.setEnabled(idx > 0 and self._job is None)
        if idx == 0:
            self._next.setText("Next →")
        elif idx == 1:
            self._next.setText("Next →")
        elif idx == 2:
            self._next.setText("Run →" if self._job is None else "Running…")
            self._next.setEnabled(self._job is None)
        else:
            self._next.setText("Open full journal →")
            self._next.setEnabled(True)
