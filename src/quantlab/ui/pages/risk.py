from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.chart_data import load_risk_exposures
from quantlab.app.queries import (
    factor_catalog_rows,
    last_factor_experiment_row,
    last_risk_experiment_row,
    risk_model_catalog_rows,
)
from quantlab.ui.widgets.charts import BarChartWidget, DashboardStrip
from quantlab.ui.widgets.data_table import fill_field_value_table, fill_table
from quantlab.ui.widgets.lab_shell import LabPageShell


class RiskPage(LabPageShell):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Risk Lab",
            subtitle=(
                "Factor exposures and covariance estimates — separate from live authorization."
            ),
            nayak_summary=(
                "Risk numbers describe uncertainty and concentration. "
                "They are not forecasts and not alpha — the live firewall stays independent."
            ),
            technical=(
                "Covariance estimation and factor IC run in the core; this page is read-only."
            ),
        )
        self._runtime = runtime
        body = self.body()
        self._dash = DashboardStrip(["Factor IC", "Est. vol", "Condition #", "Firewall"])
        body.addWidget(self._dash)
        self._bars = BarChartWidget()
        body.addWidget(self._bars)
        self.factors = QTableWidget()
        self.models = QTableWidget()
        self.last_factor = QTableWidget()
        self.last_risk = QTableWidget()
        for title, table in (
            ("Seed factors", self.factors),
            ("Research risk models", self.models),
            ("Last factor experiment", self.last_factor),
            ("Last risk experiment", self.last_risk),
        ):
            body.addWidget(self._section_label(title))
            body.addWidget(table, 1)
        self.refresh()

    @staticmethod
    def _section_label(title: str) -> QLabel:
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        label.setStyleSheet("font-weight: 600; font-size: 13px;")
        return label

    def refresh(self) -> None:
        fill_table(
            self.factors,
            ["Factor", "Category", "Source", "Lifecycle", "Identity"],
            [
                [
                    str(row["factor_id"]),
                    str(row["category"]),
                    str(row["source"]),
                    str(row["lifecycle"]),
                    str(row["identity"])[:12],
                ]
                for row in factor_catalog_rows()
            ],
            truncate_columns={4},
        )
        fill_table(
            self.models,
            ["Model", "Estimator", "Lookback", "Factors", "Identity"],
            [
                [
                    str(row["risk_model_id"]),
                    str(row["estimator"]),
                    str(row["lookback"]),
                    str(row["factors"]),
                    str(row["identity"])[:12],
                ]
                for row in risk_model_catalog_rows()
            ],
            truncate_columns={4},
        )
        factor = last_factor_experiment_row(self._runtime)
        if factor is None:
            fill_field_value_table(self.last_factor, [])
        else:
            fill_field_value_table(
                self.last_factor,
                [
                    ("experiment", str(factor["id"])[:16]),
                    ("factor", str(factor["factor_id"])),
                    ("gate", str(factor["gate_outcome"])),
                    ("data", str(factor["data_kind"])),
                    (
                        "spearman_ic",
                        "" if factor["spearman_ic"] is None else f"{factor['spearman_ic']:.4f}",
                    ),
                ],
            )
        found = last_risk_experiment_row(self._runtime)
        bar_items: list[tuple[str, float, str]] = []
        if factor and isinstance(factor.get("spearman_ic"), float):
            bar_items.append(("Factor IC", float(factor["spearman_ic"]), "#42a5f5"))
        if found is None:
            fill_field_value_table(self.last_risk, [])
            for card in self._dash.cards:
                card.set_value("—")
            self._bars.set_items(bar_items)
            return
        vol = found["estimated_volatility"]
        cond = found.get("condition_number")
        beta = found.get("beta_mean")
        exposures = load_risk_exposures(self._runtime.paths.artifacts_dir, str(found["id"]))
        for i, (name, value) in enumerate(sorted(exposures.items())[:6]):
            bar_items.append((name[:10], value, "#ffa726" if i % 2 else "#66bb6a"))
        if isinstance(vol, float):
            bar_items.append(("Vol", vol, "#ab47bc"))
        if isinstance(beta, float):
            bar_items.append(("Beta μ", beta, "#26c6da"))
        self._bars.set_items(bar_items)
        ic = factor["spearman_ic"] if factor else None
        self._dash.card(0).set_value(
            f"{ic:.3f}" if isinstance(ic, float) else "—",
            accent="#42a5f5",
        )
        self._dash.card(1).set_value(
            f"{vol:.4f}" if isinstance(vol, float) else "—",
        )
        self._dash.card(2).set_value(
            f"{cond:.1f}" if isinstance(cond, float) else "—",
            accent="#ef5350" if isinstance(cond, float) and cond > 100 else "#42a5f5",
        )
        self._dash.card(3).set_value(self._runtime.risk_state.value[:12])
        fill_field_value_table(
            self.last_risk,
            [
                ("experiment", str(found["id"])[:16]),
                ("risk_model", str(found["risk_model_id"])),
                ("factor_set", str(found["factor_set"])),
                ("gate", str(found["gate_outcome"])),
                ("data", str(found["data_kind"])),
                ("estimated_vol", "" if vol is None else f"{vol:.6f}"),
                (
                    "condition_number",
                    "" if cond is None else f"{cond:.2f}",
                ),
                ("beta_mean", "" if beta is None else f"{beta:.4f}"),
                ("firewall", self._runtime.risk_state.value),
            ],
        )
