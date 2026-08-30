from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTabWidget

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.queries import (
    fabric_calendar_rows,
    fabric_catalog_rows,
    fabric_corporate_action_rows,
    fabric_coverage_rows,
    fabric_health_rows,
    fabric_lineage_rows,
    fabric_pit_status,
    fabric_quality_rows,
    fabric_security_master_rows,
    fabric_universe_rows,
)
from quantlab.ui.widgets.charts import BarChartWidget, DashboardStrip
from quantlab.ui.widgets.data_table import fill_table
from quantlab.ui.widgets.lab_shell import LabPageShell


def _coverage_value(raw: object) -> float | None:
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        text = raw.strip().rstrip("%")
        try:
            value = float(text)
            return value / 100.0 if raw.endswith("%") and value > 1 else value
        except ValueError:
            return None
    return None


class DataPage(LabPageShell):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Data fabric",
            subtitle=(
                "Catalog, quality, security master, corporate actions, "
                "calendar, universe, and point-in-time status."
            ),
            nayak_summary=(
                "Every experiment reads from versioned datasets. "
                "Available-time rules prevent look-ahead — "
                "the fabric enforces what you can know when."
            ),
            technical="Parquet ingestion and PIT gates run in the core; this page is read-only.",
        )
        self._runtime = runtime
        body = self.body()
        self._dash = DashboardStrip(["Datasets", "Research ready", "Quarantined", "PIT ready"])
        body.addWidget(self._dash)
        self._coverage_chart = BarChartWidget()
        body.addWidget(self._coverage_chart)
        self._tabs = QTabWidget()
        self._catalog = QTableWidget()
        self._health = QTableWidget()
        self._coverage = QTableWidget()
        self._pit_table = QTableWidget()
        self._quality = QTableWidget()
        self._master = QTableWidget()
        self._actions = QTableWidget()
        self._calendar = QTableWidget()
        self._universe = QTableWidget()
        self._lineage = QTableWidget()
        self._tabs.addTab(self._catalog, "Catalog")
        self._tabs.addTab(self._health, "Health")
        self._tabs.addTab(self._coverage, "Coverage")
        self._tabs.addTab(self._pit_table, "PIT status")
        self._tabs.addTab(self._quality, "Quality")
        self._tabs.addTab(self._master, "Security master")
        self._tabs.addTab(self._actions, "Corporate actions")
        self._tabs.addTab(self._calendar, "Calendar")
        self._tabs.addTab(self._universe, "Universe")
        self._tabs.addTab(self._lineage, "Lineage")
        body.addWidget(self._tabs, 1)
        self.refresh()

    def refresh(self) -> None:
        catalog_rows = [
            [
                str(row["dataset_id"]),
                str(row["version"]),
                str(row["state"]),
                str(row["data_kind"]),
                str(row["checksum"])[:16],
                str(row["source"]),
            ]
            for row in fabric_catalog_rows(self._runtime)
        ]
        fill_table(
            self._catalog,
            ["Dataset", "Version", "State", "Kind", "Checksum", "Source"],
            catalog_rows,
            truncate_columns={4},
        )
        health_rows = [
            [str(row["name"]), str(row["value"])] for row in fabric_health_rows(self._runtime)
        ]
        fill_table(self._health, ["Check", "Value"], health_rows, badge_columns={1})
        coverage_rows = fabric_coverage_rows(self._runtime)
        fill_table(
            self._coverage,
            ["Dataset", "Coverage", "Kind", "State"],
            [
                [str(row["dataset"]), str(row["coverage"]), str(row["kind"]), str(row["state"])]
                for row in coverage_rows
            ],
        )
        pit = fabric_pit_status(self._runtime)
        fill_table(
            self._pit_table,
            ["Field", "Value"],
            [
                ["datasets", str(pit["datasets"])],
                ["research_ready", str(pit["research_ready"])],
                ["note", str(pit["note"])],
            ],
            badge_columns={1},
        )
        fill_table(
            self._quality,
            ["Dataset", "Kind", "State", "Completeness", "Note"],
            [
                [
                    str(row["dataset"]),
                    str(row["kind"]),
                    str(row["state"]),
                    str(row["completeness"]),
                    str(row["note"]),
                ]
                for row in fabric_quality_rows(self._runtime)
            ],
        )
        fill_table(
            self._master,
            ["Security", "Symbol at T", "Note"],
            [
                [str(row["security_id"]), str(row["symbol_at_T"]), str(row["note"])]
                for row in fabric_security_master_rows(self._runtime)
            ],
        )
        fill_table(
            self._actions,
            ["Type", "Announcement", "Effective", "Available", "Note"],
            [
                [
                    str(row["type"]),
                    str(row["announcement"]),
                    str(row["effective"]),
                    str(row["available"]),
                    str(row["note"]),
                ]
                for row in fabric_corporate_action_rows(self._runtime)
            ],
        )
        fill_table(
            self._calendar,
            ["Dataset", "Calendar", "Source", "Note"],
            [
                [
                    str(row["dataset"]),
                    str(row["calendar"]),
                    str(row["source"]),
                    str(row["note"]),
                ]
                for row in fabric_calendar_rows(self._runtime)
            ],
        )
        fill_table(
            self._universe,
            ["Universe", "As of", "Note"],
            [
                [str(row["universe_id"]), str(row["as_of"]), str(row["note"])]
                for row in fabric_universe_rows(self._runtime)
            ],
        )
        fill_table(
            self._lineage,
            ["Dataset", "Source", "Checksum", "CA policy", "Note"],
            [
                [
                    str(row["dataset"]),
                    str(row["source"]),
                    str(row["checksum"]),
                    str(row["ca_policy"]),
                    str(row["note"]),
                ]
                for row in fabric_lineage_rows(self._runtime)
            ],
            truncate_columns={2},
        )

        ready = pit.get("research_ready", 0)
        total = pit.get("datasets", len(catalog_rows))
        quarantined = sum(1 for row in catalog_rows if row[2] == "quarantined")
        self._dash.card(0).set_value(str(total))
        self._dash.card(1).set_value(str(ready), accent="#66bb6a")
        quarantined_accent = "#ef5350" if quarantined else "#42a5f5"
        self._dash.card(2).set_value(str(quarantined), accent=quarantined_accent)
        self._dash.card(3).set_value(f"{ready}/{total}")

        bar_items: list[tuple[str, float, str]] = []
        colors = ("#42a5f5", "#66bb6a", "#ffa726", "#ab47bc", "#26c6da", "#ef5350")
        for i, row in enumerate(coverage_rows[:8]):
            value = _coverage_value(row.get("coverage"))
            if value is None:
                continue
            label = str(row["dataset"]).split("@")[0][:10]
            bar_items.append((label, value, colors[i % len(colors)]))
        self._coverage_chart.set_items(bar_items)
