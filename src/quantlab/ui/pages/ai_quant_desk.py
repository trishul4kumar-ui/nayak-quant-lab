"""Native, accessible entry point for the research-only agent foundation."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from PySide6.QtWidgets import QLabel, QPushButton, QTabWidget, QTextBrowser

from quantlab.agents.contracts import AgentRole, AgentRunRecord, AgentState
from quantlab.agents.permissions import mandate_for
from quantlab.agents.presentation import AgentDeskPresentationService, AgentVisualStateDTO
from quantlab.agents.provider import configured_provider
from quantlab.agents.repository import AgentRepository
from quantlab.agents.tool_gateway import AgentToolGateway
from quantlab.ai.permissions import DENIED_CAPABILITIES
from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.ui.widgets.agent_desk_webview import AgentDeskWebView
from quantlab.ui.widgets.lab_shell import LabPageShell


class AiQuantDeskPage(LabPageShell):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "AI Quant Desk",
            subtitle="Bull / Bear · research contracts and evidence history",
            nayak_summary="Research permissions are enforced in code. Live authority stays with "
            "the existing human execution controls.",
        )
        self.runtime = runtime
        self._repo_path = runtime.paths.database_dir / "agent_desk.sqlite"
        self._provider = configured_provider()
        self._status = QLabel()
        self._status.setObjectName("deskProviderStatus")
        self._status.setWordWrap(True)
        self.body().addWidget(self._status)
        self._visual = AgentDeskWebView()
        self._visual.bridge.navigationRequested.connect(self._visual_navigation)
        self.body().addWidget(self._visual)
        self._tabs = QTabWidget()
        self._tabs.setAccessibleName("AI desk foundation inspectors")
        self._inspectors: dict[str, QTextBrowser] = {}
        for name in ("Bull", "Bear", "Permissions", "Tools", "Audit"):
            inspector = QTextBrowser()
            inspector.setOpenExternalLinks(False)
            inspector.setAccessibleName(f"{name} research inspector")
            self._tabs.addTab(inspector, name)
            self._inspectors[name] = inspector
        self.body().addWidget(self._tabs, 1)
        refresh = QPushButton("Refresh desk status")
        refresh.clicked.connect(self.refresh)
        self.add_toolbar_widget(refresh)
        self.refresh()

    def _visual_navigation(self, intent: str, identity: str) -> None:
        if intent == "select_agent":
            self._tabs.setCurrentIndex(0 if identity == "BULL" else 1)

    def refresh(self) -> None:
        health = self._provider.health()
        self._status.setText(
            f"Provider: {health.provider} / {health.model} · {health.observed_status} · "
            "AI LIVE ORDER AUTHORITY: DENIED"
        )
        try:
            repository = AgentRepository(self._repo_path)
            try:
                runs = repository.list(AgentRunRecord)
                presentation = AgentDeskPresentationService()
                states = []
                for role, label in ((AgentRole.BULL, "Bull"), (AgentRole.BEAR, "Bear")):
                    role_runs = []
                    from quantlab.agents.contracts import AgentRunContext

                    for run in runs:
                        context = repository.get(run.context_hash, AgentRunContext)
                        if context.agent.role is role:
                            role_runs.append(run)
                    latest = role_runs[-1] if role_runs else None
                    states.append(presentation.from_run(role, latest))
                    self._inspectors[label].setPlainText(
                        json.dumps(
                            [row.model_dump(mode="json") for row in role_runs[-50:]],
                            indent=2,
                        )
                        if role_runs
                        else "No analyst runs yet. Phase 39 establishes contracts."
                    )
                mandate = mandate_for(AgentRole.BULL, created_at=datetime(2026, 10, 4, tzinfo=UTC))
                self._inspectors["Permissions"].setPlainText(
                    json.dumps(
                        {
                            "allowed": sorted(mandate.granted),
                            "permanently_denied": sorted(DENIED_CAPABILITIES),
                        },
                        indent=2,
                    )
                )
                self._inspectors["Tools"].setPlainText(
                    json.dumps(
                        [
                            {"tool": tool, "capability": capability, "adapter_bound": bound}
                            for tool, capability, bound in AgentToolGateway(
                                repository, mandate
                            ).catalog()
                        ],
                        indent=2,
                    )
                )
                self._inspectors["Audit"].setPlainText(
                    json.dumps(
                        [row.model_dump(mode="json") for row in repository.audit_events()[-100:]],
                        indent=2,
                    )
                )
                self._visual.bridge.publish(tuple(states), ())
            finally:
                repository.close()
        except (OSError, RuntimeError, ValueError, KeyError):
            self._status.setText("DESK BLOCKED · research persistence could not be verified")
            for inspector in self._inspectors.values():
                inspector.setPlainText("Persistence unavailable. Research runs are blocked.")
            self._visual.bridge.publish(
                tuple(
                    AgentVisualStateDTO(
                        agent=role,
                        state=AgentState.BLOCKED,
                        task_label="Persistence unavailable",
                        completed_tools=0,
                    )
                    for role in AgentRole
                ),
                (),
            )
