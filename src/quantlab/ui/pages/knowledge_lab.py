from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QLabel, QTableWidget

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.knowledge import edge_table_rows, last_snapshot_row, node_table_rows
from quantlab.ui.widgets.catalog_page import CatalogLabPage
from quantlab.ui.widgets.charts import GraphPreviewWidget
from quantlab.ui.widgets.data_table import fill_table


class KnowledgeLabPage(CatalogLabPage):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Knowledge Lab",
            subtitle="What the lab has learned — not what it is allowed to trade.",
            nayak_summary=(
                "Knowledge is memory, not authority. Failed hypotheses stay searchable. "
                "Synthetic evidence cannot become validated market knowledge. "
                "AI text is never empirical evidence."
            ),
            technical=(
                "The graph is a query view of quantlab.knowledge. "
                "Qt does not parse Parquet, query DuckDB, run GP, or write the ledger."
            ),
            catalog_title="Knowledge nodes",
            catalog_headers=["Id", "Type", "Status", "Identity"],
            last_title="Last knowledge snapshot",
            empty_title="No knowledge snapshot yet",
            empty_body=(
                "Seed memory loads on first inspect. Run quantlab knowledge snapshot to freeze."
            ),
            empty_action=None,
            dashboard_titles=["Nodes", "Edges", "Snapshots", "Graph hash"],
        )
        self._runtime = runtime
        self._graph = GraphPreviewWidget()
        self.body().insertWidget(2, self._graph)
        self._type_filter = QComboBox()
        self._type_filter.addItems(
            [
                "all",
                "hypothesis",
                "expression",
                "evidence",
                "research_claim",
                "dead_end",
                "experiment",
                "discovery_run",
            ]
        )
        self._type_filter.currentTextChanged.connect(self.refresh)
        self.add_toolbar_widget(QLabel("Type"))
        self.add_toolbar_widget(self._type_filter)
        self._rel_filter = QComboBox()
        self._rel_filter.addItems(
            [
                "all",
                "uses_feature",
                "tested_by",
                "evidence_for",
                "falsified_by",
                "member_of",
                "supports",
            ]
        )
        self._rel_filter.currentTextChanged.connect(self.refresh)
        self.add_toolbar_widget(QLabel("Edge"))
        self.add_toolbar_widget(self._rel_filter)

        edge_label = QLabel("Relationships (table)")
        edge_label.setObjectName("sectionTitle")
        edge_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        self.edges = QTableWidget()
        self.insert_before_last_run(self.edges, label=edge_label)
        self.refresh()

    def refresh(self) -> None:
        node_type = self._type_filter.currentText() if hasattr(self, "_type_filter") else "all"
        rel = self._rel_filter.currentText() if hasattr(self, "_rel_filter") else "all"
        self.set_catalog_rows(node_table_rows(node_type=node_type))
        edge_rows = edge_table_rows(relationship=rel)
        fill_table(
            self.edges,
            ["Source", "Relationship", "Target", "Basis"],
            edge_rows,
            truncate_columns={0, 2},
        )
        graph_edges = [
            (str(row[0]), str(row[1]), str(row[2]))
            for row in edge_rows
            if len(row) >= 3
        ]
        self._graph.set_edges(graph_edges)
        last = last_snapshot_row()
        dash = self.dashboard
        if last is None or dash is None:
            self.set_last_run(None)
            if dash is not None:
                for card in dash.cards:
                    card.set_value("—")
            return
        dash.card(0).set_value(str(last.get("nodes", "—")))
        dash.card(1).set_value(str(last.get("edges", "—")))
        dash.card(2).set_value("1")
        dash.card(3).set_value(str(last.get("hash", "—"))[:12])
        self.set_last_run(
            [
                ("Snapshot", str(last["id"])),
                ("Graph hash", str(last["hash"])),
                ("Nodes", str(last["nodes"])),
                ("Edges", str(last["edges"])),
                ("Software", str(last["version"])),
                ("Note", "Memory, not a live book."),
            ]
        )
