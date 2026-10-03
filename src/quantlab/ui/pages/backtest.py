from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QVBoxLayout,
)

from quantlab.app.assistant import NayakAssistant
from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.chart_data import (
    drawdown_episode_rows,
    drawdown_from_equity,
    equity_chart_series,
)
from quantlab.app.copy import SYNTHETIC_SHARPE_DISCLAIMER
from quantlab.app.jobs import Job, JobStatus
from quantlab.app.settings_store import ExperienceMode
from quantlab.ui.widgets import ExplainChip, TerminalGrid, TerminalPanel
from quantlab.ui.widgets.charts import DashboardStrip, DrawdownChartWidget, MultiSeriesChartWidget
from quantlab.ui.widgets.data_table import fill_table
from quantlab.ui.widgets.lab_shell import LabPageShell


class BacktestPage(LabPageShell):
    def __init__(self, runtime: ApplicationRuntime, on_done: Callable[[], None]) -> None:
        super().__init__(
            "Backtest Lab",
            subtitle="Run the momentum slice on synthetic NSE-style data.",
            nayak_summary=(
                "Same-bar fills are forbidden — every trade fills on the next bar after costs. "
                f"{SYNTHETIC_SHARPE_DISCLAIMER}"
            ),
        )
        self._runtime = runtime
        self._on_done = on_done
        self._job: Job | None = None
        self._last_experiment_id = ""
        self._assistant = NayakAssistant(runtime)

        prefs = runtime.ui_settings.current
        self.n_days = QSpinBox()
        self.n_days.setRange(40, 400)
        self.n_days.setValue(prefs.last_n_days)
        self.lookback = QSpinBox()
        self.lookback.setRange(5, 60)
        self.lookback.setValue(prefs.last_lookback)
        self.top_n = QSpinBox()
        self.top_n.setRange(1, 5)
        self.top_n.setValue(prefs.last_top_n)
        self.cost_bps = QDoubleSpinBox()
        self.cost_bps.setRange(0.1, 100.0)
        self.cost_bps.setDecimals(1)
        self.cost_bps.setValue(prefs.last_cost_bps)

        form = QFormLayout()
        form.addRow("Strategy", QLabel("cs_momentum_v1"))
        form.addRow("Universe", QLabel("synthetic NSE (5 names)"))
        form.addRow("Fill", QLabel("next bar only"))
        form.addRow(ExplainChip("n_days", label="Days"), self.n_days)
        form.addRow(ExplainChip("lookback", label="Lookback"), self.lookback)
        form.addRow(ExplainChip("top_n", label="Top N"), self.top_n)
        form.addRow(ExplainChip("cost_bps", label="Cost bps"), self.cost_bps)

        self.run_btn = QPushButton("Run backtest")
        self.run_btn.setObjectName("primary")
        self.run_btn.setDefault(True)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.run_btn.clicked.connect(self._start)
        self.cancel_btn.clicked.connect(self._cancel)
        self.add_toolbar_widget(self.run_btn)
        self.add_toolbar_widget(self.cancel_btn)

        body = self.body()
        form_host = QVBoxLayout()
        form_host.addLayout(form)
        body.addLayout(form_host)

        self._dash = DashboardStrip(["Sharpe", "Return", "Max DD", "Gate"])
        body.addWidget(self._dash)

        self.status = QLabel("Idle")
        self.status.setObjectName("nayakVoice")
        body.addWidget(self.status)

        self.curve = MultiSeriesChartWidget()
        self.curve.set_empty_message("Run a backtest to see equity vs cash benchmark")
        self.drawdown = DrawdownChartWidget()
        self.metrics = QTableWidget()
        self.integrity = QTableWidget()
        self.dd_episodes = QTableWidget()
        cols = 1 if prefs.experience_mode is ExperienceMode.GUIDED else 2
        self._terminal = TerminalGrid(
            columns=cols,
            layout_id="backtest",
            settings=runtime.ui_settings,
        )
        self._terminal.set_panels(
            [
                TerminalPanel("Equity curve", self.curve, explain_key="equity_curve"),
                TerminalPanel("Drawdown", self.drawdown, explain_key="max_drawdown"),
                TerminalPanel("Top drawdowns", self.dd_episodes, explain_key="max_drawdown"),
                TerminalPanel("Metrics", self.metrics, explain_key="sharpe"),
                TerminalPanel("Integrity", self.integrity, explain_key="integrity"),
            ]
        )
        body.addWidget(self._terminal, 1)

        note_card = QFrame()
        note_card.setObjectName("card")
        note_layout = QVBoxLayout(note_card)
        note_layout.setContentsMargins(12, 10, 12, 10)
        note_title = QLabel("Journal note")
        note_title.setStyleSheet("font-weight: 600;")
        self._quick_note = QPlainTextEdit()
        self._quick_note.setPlaceholderText("Optional — what did this run teach you?")
        self._quick_note.setMaximumHeight(64)
        note_row = QHBoxLayout()
        self._save_note = QPushButton("Save note")
        self._save_note.setEnabled(False)
        self._save_note.setToolTip("Run a backtest before saving a journal note")
        self._save_note.clicked.connect(self._save_quick_note)
        self._note_status = QLabel()
        self._note_status.setObjectName("nayakVoice")
        note_row.addWidget(self._save_note)
        note_row.addWidget(self._note_status)
        note_row.addStretch()
        note_layout.addWidget(note_title)
        note_layout.addWidget(self._quick_note)
        note_layout.addLayout(note_row)
        body.addWidget(note_card)

    def _start(self) -> None:
        prefs = self._runtime.ui_settings.current
        prefs.last_n_days = self.n_days.value()
        prefs.last_lookback = self.lookback.value()
        prefs.last_top_n = self.top_n.value()
        prefs.last_cost_bps = float(self.cost_bps.value())
        self._runtime.ui_settings.save(prefs)
        self._job = self._runtime.submit_momentum_backtest(
            {
                "n_days": self.n_days.value(),
                "lookback": self.lookback.value(),
                "top_n": self.top_n.value(),
                "cost_bps": float(self.cost_bps.value()),
            }
        )
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status.setText(f"Queued {self._job.job_id[:8]}")

    def _cancel(self) -> None:
        if self._job is not None:
            self._runtime.jobs.cancel(self._job.job_id)
            self.status.setText("Cancelling…")

    def poll(self) -> None:
        if self._job is None:
            return
        job = self._runtime.jobs.get(self._job.job_id)
        if job is None:
            return
        self.status.setText(f"{job.status.value}  progress={job.progress:.0%}")
        if job.status in {JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.CANCELLING}:
            self.set_running(f"Backtest {job.status.value} — {job.progress:.0%}")
        elif job.status is JobStatus.COMPLETED:
            self.set_running(None)
            self._show_result(job)
            self._job = None
            self.run_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self._runtime.record_notification("Backtest completed")
            self._on_done()
        elif job.status in {JobStatus.FAILED, JobStatus.CANCELLED}:
            self.set_running(None)
            self.status.setText(f"{job.status.value}: {job.error or ''}")
            self._job = None
            self.run_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)

    def _show_result(self, job: Job) -> None:
        result = job.result
        equity = [float(x) for x in result.get("equity_curve", [])]
        self.curve.set_series(
            equity_chart_series(equity, strategy_label="Strategy", include_benchmark=True)
        )
        self.drawdown.set_drawdown(drawdown_from_equity(equity))
        fill_table(
            self.dd_episodes,
            ["Peak", "Trough", "Depth", "Duration", "Recovery"],
            drawdown_episode_rows(equity),
        )
        metrics = result.get("metrics") or {}
        exp_id = str(result.get("experiment_id", ""))
        self._last_experiment_id = exp_id
        prefs = self._runtime.ui_settings.current
        self._quick_note.setPlainText(prefs.journal_notes.get(exp_id, ""))
        self._save_note.setEnabled(bool(exp_id))
        self._note_status.setText(SYNTHETIC_SHARPE_DISCLAIMER)
        metric_rows = [
            [k, f"{v:.6f}" if isinstance(v, float) else str(v)] for k, v in metrics.items()
        ]
        metric_rows.insert(0, ["experiment_id", exp_id[:16]])
        metric_rows.append(["conclusion", str(result.get("conclusion", ""))])
        fill_table(
            self.metrics, ["Metric", "Value"], metric_rows, experiment_links={(0, 1): exp_id}
        )
        integrity = result.get("integrity") or {}
        fill_table(
            self.integrity,
            ["Check", "Result"],
            [[k, str(v)] for k, v in integrity.items()],
            badge_columns={1},
        )
        sharpe = metrics.get("sharpe")
        total_return = metrics.get("total_return")
        max_dd = metrics.get("max_drawdown")
        self._dash.card(0).set_value(
            f"{sharpe:.2f}" if isinstance(sharpe, float) else "—",
            accent="#42a5f5",
        )
        self._dash.card(1).set_value(
            f"{total_return:.2%}" if isinstance(total_return, float) else "—",
        )
        self._dash.card(2).set_value(
            f"{max_dd:.2%}" if isinstance(max_dd, float) else "—",
            accent="#ef5350" if isinstance(max_dd, float) and max_dd < -0.05 else "#42a5f5",
        )
        self._dash.card(3).set_value(str(result.get("status", "completed"))[:12])
        self.status.setText(f"Completed · experiment {exp_id[:8]} saved to ledger")

    def _save_quick_note(self) -> None:
        if not self._last_experiment_id:
            return
        if self._assistant.save_journal_note(
            self._last_experiment_id,
            self._quick_note.toPlainText(),
        ):
            self._note_status.setText("Note saved to journal.")

    def save_terminal_layout(self) -> None:
        self._terminal.persist_layout()
