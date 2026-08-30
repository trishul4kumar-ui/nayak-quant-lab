from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QTableWidget, QVBoxLayout

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.chart_data import (
    drawdown_episode_rows,
    drawdown_from_equity,
    equity_chart_series,
    latest_equity,
    load_equity_curve,
    load_validation_benchmark,
)
from quantlab.app.jobs import Job, JobStatus
from quantlab.app.queries import last_validation_row
from quantlab.app.validation_summary import validation_two_questions
from quantlab.ui.widgets import ExplainChip, TerminalGrid, TerminalPanel
from quantlab.ui.widgets.charts import DashboardStrip, DrawdownChartWidget, MultiSeriesChartWidget
from quantlab.ui.widgets.data_table import fill_table
from quantlab.ui.widgets.lab_shell import LabPageShell


class ValidationPage(LabPageShell):
    def __init__(self, runtime: ApplicationRuntime, on_done: Callable[[], None]) -> None:
        super().__init__(
            "Validation",
            subtitle="Walk-forward, robustness, bootstrap, and the research promotion gate.",
            nayak_summary=(
                "A single backtest can lie. Validation stress-tests the idea across windows "
                "and cost assumptions. Synthetic results still cannot be promoted to live."
            ),
        )
        self._runtime = runtime
        self._on_done = on_done
        self._job: Job | None = None

        self.run_btn = QPushButton("Run validation suite")
        self.run_btn.setObjectName("primary")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.run_btn.clicked.connect(self._start)
        self.cancel_btn.clicked.connect(self._cancel)
        self.add_toolbar_widget(ExplainChip("validation", label="What is this?"))
        self.add_toolbar_widget(self.run_btn)
        self.add_toolbar_widget(self.cancel_btn)

        body = self.body()
        self._two_q = QFrame()
        self._two_q.setObjectName("nayakTip")
        two_layout = QVBoxLayout(self._two_q)
        two_layout.setContentsMargins(14, 12, 14, 12)
        two_head = QLabel("Two questions every validation must answer")
        two_head.setStyleSheet("font-weight: 600;")
        self._profit_q = QLabel()
        self._profit_q.setWordWrap(True)
        self._rules_q = QLabel()
        self._rules_q.setWordWrap(True)
        two_layout.addWidget(two_head)
        two_layout.addWidget(self._profit_q)
        two_layout.addWidget(self._rules_q)
        body.addWidget(self._two_q)

        self._dash = DashboardStrip(["Sharpe", "OOS windows", "Gate", "Excess vs cash"])
        body.addWidget(self._dash)

        self.status = QLabel("Idle")
        self.status.setObjectName("nayakVoice")
        body.addWidget(self.status)

        self.summary = QTableWidget()
        self.gate = QTableWidget()
        self.curve = MultiSeriesChartWidget()
        self.curve.set_empty_message("Run validation to compare strategy vs cash benchmark")
        self.drawdown = DrawdownChartWidget()
        self.dd_episodes = QTableWidget()
        self._terminal = TerminalGrid(
            columns=2,
            layout_id="validation",
            settings=runtime.ui_settings,
        )
        self._terminal.set_panels(
            [
                TerminalPanel("Equity curve", self.curve, explain_key="equity_curve"),
                TerminalPanel("Drawdown", self.drawdown, explain_key="max_drawdown"),
                TerminalPanel("Top drawdowns", self.dd_episodes, explain_key="max_drawdown"),
                TerminalPanel("Last validation", self.summary, explain_key="validation"),
                TerminalPanel("Gate reasons", self.gate, explain_key="gate_outcome"),
            ]
        )
        body.addWidget(self._terminal, 1)
        self.refresh()

    def _start(self) -> None:
        self._job = self._runtime.submit_momentum_validation(
            {
                "n_days": 80,
                "lookback": 20,
                "top_n": 2,
                "cost_bps": 10.0,
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
            self.set_running(f"Validation {job.status.value} — {job.progress:.0%}")
        elif job.status is JobStatus.COMPLETED:
            self.set_running(None)
            self._job = None
            self.run_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self._runtime.record_notification("Validation completed")
            self.refresh()
            self._on_done()
        elif job.status in {JobStatus.FAILED, JobStatus.CANCELLED}:
            self.set_running(None)
            self.status.setText(f"{job.status.value}: {job.error or ''}")
            self._job = None
            self.run_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)

    def refresh(self) -> None:
        summary = validation_two_questions(self._runtime)
        tone_styles = {
            "ok": "color: #26a69a; font-weight: 600;",
            "warn": "color: #ffb74d; font-weight: 600;",
            "bad": "color: #ef5350; font-weight: 600;",
            "neutral": "color: #9aa1ad;",
        }
        self._profit_q.setText(f"1. Will I reach the profit target? {summary.profit_line}")
        self._profit_q.setStyleSheet(tone_styles.get(summary.profit_tone, tone_styles["neutral"]))
        self._rules_q.setText(f"2. Am I breaking my rules? {summary.rules_line}")
        self._rules_q.setStyleSheet(tone_styles.get(summary.rules_tone, tone_styles["neutral"]))

        row = last_validation_row(self._runtime)
        if row is None:
            fill_table(self.summary, ["Field", "Value"], [["status", "no experiments yet"]])
            fill_table(self.gate, ["Check", "Result"], [])
            fill_table(self.dd_episodes, ["Peak", "Trough", "Depth", "Duration", "Recovery"], [])
            self.curve.set_series([])
            self.drawdown.set_drawdown([])
            for card in self._dash.cards:
                card.set_value("—")
                card.clear_target_progress()
            return
        exp_id = str(row["id"])
        equity = load_equity_curve(self._runtime.paths.artifacts_dir, exp_id)
        if equity is None:
            latest = latest_equity(self._runtime)
            equity = latest[1] if latest else []
        if equity:
            self.curve.set_series(
                equity_chart_series(equity, strategy_label="Strategy", include_benchmark=True)
            )
            self.drawdown.set_drawdown(drawdown_from_equity(equity))
            fill_table(
                self.dd_episodes,
                ["Peak", "Trough", "Depth", "Duration", "Recovery"],
                drawdown_episode_rows(equity),
            )
        else:
            self.curve.set_series([])
            self.drawdown.set_drawdown([])
            fill_table(self.dd_episodes, ["Peak", "Trough", "Depth", "Duration", "Recovery"], [])

        bench = load_validation_benchmark(self._runtime.paths.artifacts_dir, exp_id)
        excess = bench.get("excess_return") if bench else None
        sharpe = row.get("sharpe")
        gate = str(row.get("gate_outcome") or "(slice only)")
        self._dash.card(0).set_value(
            f"{sharpe:.2f}" if isinstance(sharpe, float) else "—",
            accent="#42a5f5",
        )
        if isinstance(sharpe, float):
            self._dash.card(0).set_target_progress(
                sharpe,
                1.0,
                headroom_label=f"{'Above' if sharpe >= 1.0 else 'Below'} 1.0 target",
            )
        self._dash.card(1).set_value(str(row.get("oos_windows", "—")))
        self._dash.card(2).set_value(gate[:14])
        if gate.lower() == "pass":
            self._dash.card(2).set_subtitle("Rules intact")
        elif gate.lower() in {"fail", "failed"}:
            self._dash.card(2).set_subtitle("Rules breached")
        self._dash.card(3).set_value(
            f"{excess:.2%}" if isinstance(excess, float) else "—",
            accent="#66bb6a" if isinstance(excess, float) and excess >= 0 else "#ef5350",
        )

        exp_id = str(row["id"])
        fill_table(
            self.summary,
            ["Field", "Value"],
            [
                ["experiment", exp_id[:16]],
                ["name", str(row["name"])],
                ["gate", gate],
                ["data", str(row["data_kind"])],
                ["config", str(row["config_hash"])[:16]],
                ["oos_windows", str(row["oos_windows"])],
                ["sharpe", "" if row["sharpe"] is None else f"{row['sharpe']:.4f}"],
            ],
            badge_columns={1},
            truncate_columns={0, 4},
            experiment_links={(0, 1): exp_id},
        )
        reasons = row.get("gate_reasons") or {}
        fill_table(
            self.gate,
            ["Check", "Result"],
            [[str(k), str(v)] for k, v in reasons.items()],
            badge_columns={1},
        )

    def save_terminal_layout(self) -> None:
        self._terminal.persist_layout()
