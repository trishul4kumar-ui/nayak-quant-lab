"""Read-only native inspector for deterministic level-plan artifacts."""

from __future__ import annotations

from datetime import UTC, datetime

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QTextBrowser, QVBoxLayout, QWidget

from quantlab.trade_levels.engine import (
    chart_overlay,
    default_trade_level_policy,
    evaluate_plan_freshness,
)
from quantlab.trade_levels.models import ExitPolicy, TradeLevelPlan


class TradeLevelWorkspace(QWidget):
    """Displays frozen plans only; it intentionally exposes no order controls."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.summary = QLabel(
            "No frozen level plan · canonical market/risk inputs are required · "
            "NO EXECUTION AUTHORITY"
        )
        self.summary.setWordWrap(True)
        self.summary.setAccessibleName("Deterministic trade level plan status")
        layout.addWidget(self.summary)
        controls = QHBoxLayout()
        self.history = QComboBox()
        self.history.setAccessibleName("Saved immutable deterministic level plans")
        controls.addWidget(self.history, 1)
        layout.addLayout(controls)
        self.details = QTextBrowser()
        self.details.setOpenExternalLinks(False)
        self.details.setAccessibleName("Level plan, chart overlay, lineage and staleness inspector")
        layout.addWidget(self.details, 1)

    def display(self, plan: TradeLevelPlan, exit_policy: ExitPolicy | None) -> None:
        now = datetime.now(UTC)
        if plan.status.value == "NO_VALID_ENTRY":
            freshness = "NO VALID ENTRY"
        else:
            freshness = evaluate_plan_freshness(
                plan,
                default_trade_level_policy(),
                now=now,
                current_price=plan.preferred_reference_price or 1,
                current_atr=plan.reference_atr or 1,
                current_regime=plan.reference_regime or "UNKNOWN",
            ).status.value
        self.summary.setText(
            f"{plan.status} · {plan.direction} · {freshness} · "
            "RESEARCH LEVELS ONLY · NO EXECUTION AUTHORITY"
        )
        overlay = chart_overlay(plan)
        self.details.setPlainText(
            "CHART OVERLAY (presentation only)\n"
            f"Entry band: {overlay.entry_zone_low} — {overlay.entry_zone_high}\n"
            f"Hard invalidation: {overlay.hard_invalidation}\n"
            f"Protective stop: {overlay.protective_stop}\n"
            f"Targets: {', '.join(str(target) for target in overlay.targets) or 'None'}\n"
            f"Trailing: {overlay.trailing_rule or 'None'}\n"
            f"Time horizon: {overlay.time_horizon or 'None'}\n\n"
            "RAW FROZEN INPUT LINEAGE\n"
            f"Plan: {plan.content_hash}\nAdjudication: {plan.adjudication_hash}\n"
            f"Snapshot: {plan.snapshot_hash}\nPolicy: {plan.level_policy_hash}\n"
            f"Price basis: {plan.price_basis} / {plan.adjustment_policy_id}\n"
            f"Tick size: {plan.tick_size}\n"
            f"Required state: {', '.join(plan.required_market_state)}\n\n"
            "EXIT POLICY\n"
            + (
                "\n".join(f"{rule.rule}: {rule.condition}" for rule in exit_policy.rules)
                if exit_policy
                else "None — no valid entry"
            )
            + "\n\nWARNINGS\n"
            + "\n".join(plan.warnings + plan.not_tested)
        )
