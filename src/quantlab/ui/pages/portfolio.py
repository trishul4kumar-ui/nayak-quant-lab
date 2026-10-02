from __future__ import annotations

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.live_ops import target_holdings
from quantlab.app.queries import last_portfolio_experiment_row, portfolio_catalog_rows
from quantlab.ui.widgets.catalog_page import CatalogLabPage
from quantlab.ui.widgets.charts import BarChartWidget, DonutChartWidget
from quantlab.ui.widgets.data_table import fill_table


class PortfolioPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Portfolio Lab",
            subtitle="Turn ensemble scores into target weights — research construction only.",
            nayak_summary=(
                "Portfolios allocate capital across names. A rejected or infeasible result "
                "is still valid research — synthetic Sharpe is not market evidence."
            ),
            technical=(
                "Constructors read from the seed catalog; the risk firewall is never bypassed here."
            ),
            catalog_title="Seed portfolios",
            catalog_headers=["Portfolio", "Ensemble", "Constructor", "Rebalance", "Identity"],
            last_title="Last portfolio experiment",
            dashboard_titles=["Sharpe", "Gross", "Net", "Turnover"],
        )
        self._runtime = runtime
        self._bars = BarChartWidget()
        self._donut = DonutChartWidget()
        body = self.body()
        body.insertWidget(2, self._donut)
        body.insertWidget(3, self._bars)

        from PySide6.QtWidgets import QLabel, QTableWidget

        live_label = QLabel("Live book (targets / paper demo)")
        live_label.setObjectName("sectionTitle")
        live_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        self._live_note = QLabel()
        self._live_note.setWordWrap(True)
        self._live_note.setObjectName("nayakVoice")
        self._holdings = QTableWidget()
        self._weight_chart = BarChartWidget()
        self.insert_before_last_run(self._weight_chart, label=live_label)
        body = self.body()
        idx = body.indexOf(self._weight_chart)
        body.insertWidget(idx + 1, self._live_note)
        body.insertWidget(idx + 2, self._holdings)
        self.refresh()

    def refresh(self) -> None:
        rows = [
            [
                str(row["portfolio_id"]),
                str(row["ensemble_id"]),
                str(row["constructor"]),
                str(row["rebalance"]),
                str(row["identity"])[:12],
            ]
            for row in portfolio_catalog_rows()
        ]
        self.set_catalog_rows(rows)
        found = last_portfolio_experiment_row(self._runtime)
        dash = self.dashboard
        if found is None or dash is None:
            self.set_last_run(None)
            if dash is not None:
                for card in dash.cards:
                    card.set_value("—")
            self._bars.set_items([])
            self._donut.set_slices([])
            return
        sharpe = found["sharpe"]
        gross = found.get("gross")
        net = found.get("net")
        turnover = found.get("turnover")
        dash.card(0).set_value(
            f"{sharpe:.2f}" if isinstance(sharpe, float) else "—",
            accent="#42a5f5",
        )
        dash.card(1).set_value(
            f"{gross:.3f}" if isinstance(gross, float) else "—",
        )
        dash.card(2).set_value(
            f"{net:.3f}" if isinstance(net, float) else "—",
            accent="#66bb6a" if isinstance(net, float) and net >= 0 else "#ef5350",
        )
        dash.card(3).set_value(
            f"{turnover:.3f}" if isinstance(turnover, float) else "—",
        )
        bar_items: list[tuple[str, float, str]] = []
        if isinstance(gross, float):
            bar_items.append(("Gross", gross, "#42a5f5"))
        if isinstance(net, float):
            bar_items.append(("Net", net, "#66bb6a"))
        if isinstance(turnover, float):
            bar_items.append(("Turn", turnover, "#ffa726"))
        if isinstance(sharpe, float):
            bar_items.append(("Sharpe", sharpe, "#ab47bc"))
        self._bars.set_items(bar_items)

        holdings, live_note = target_holdings(self._runtime)
        if holdings:
            self._live_note.setText(live_note)
            self._live_note.setVisible(True)
            self._holdings.setVisible(True)
            self._weight_chart.setVisible(True)
            fill_table(
                self._holdings,
                ["Instrument", "Weight", "Notional", "PnL", "Source"],
                [
                    [
                        str(row["instrument"]),
                        str(row["weight_pct"]),
                        f"{row['notional']:,.0f}",
                        str(row["pnl"]),
                        str(row["source"]),
                    ]
                    for row in holdings
                ],
            )
            self._weight_chart.set_items(
                [
                    (str(row["instrument"]).replace("NSE:", ""), float(row["weight"]), "#42a5f5")
                    for row in holdings
                    if row["instrument"] != "CASH"
                ]
            )
            slice_colors = ("#42a5f5", "#66bb6a", "#ffa726", "#ab47bc", "#26c6da", "#ef5350")
            self._donut.set_slices(
                [
                    (
                        str(row["instrument"]).replace("NSE:", ""),
                        float(row["weight"]),
                        slice_colors[i % len(slice_colors)],
                    )
                    for i, row in enumerate(holdings)
                    if row["instrument"] != "CASH" and float(row["weight"]) > 0
                ]
            )
        else:
            self._live_note.setText(
                "No holdings yet — run Capital Lab allocate or complete the Broker paper wizard."
            )
            self._live_note.setVisible(True)
            self._holdings.setVisible(False)
            self._weight_chart.set_items([])
            self._donut.set_slices([])

        self.set_last_run(
            [
                ("experiment", str(found["id"])[:16]),
                ("portfolio", str(found["portfolio_id"])),
                ("ensemble", str(found["ensemble_id"])),
                ("optimizer", str(found["optimizer"])),
                ("gate", str(found["gate_outcome"])),
                ("data", str(found["data_kind"])),
                ("sharpe", "" if sharpe is None else f"{sharpe:.4f}"),
                ("gross", "" if found["gross"] is None else f"{found['gross']:.4f}"),
                ("net", "" if found["net"] is None else f"{found['net']:.4f}"),
                ("turnover", "" if found["turnover"] is None else f"{found['turnover']:.4f}"),
            ]
        )
