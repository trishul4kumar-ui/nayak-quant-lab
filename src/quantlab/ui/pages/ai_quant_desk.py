"""Native, accessible entry point for the research-only agent foundation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QCheckBox, QFileDialog, QLabel, QPushButton, QTabWidget, QTextBrowser

from quantlab.agents.bear import BearWorker, bear_mandate, create_bear_context, search_bear_history
from quantlab.agents.bull import BullWorker, bull_mandate, create_bull_context, search_bull_history
from quantlab.agents.contracts import (
    AgentRole,
    AgentRunContext,
    AgentRunRecord,
    AgentState,
    ResearchMode,
)
from quantlab.agents.inputs import read_history, read_snapshot
from quantlab.agents.presentation import (
    AgentDeskPresentationService,
    AgentVisualStateDTO,
    EvidenceNodeSummaryDTO,
)
from quantlab.agents.provider import configured_provider
from quantlab.agents.repository import AgentRepository
from quantlab.agents.research import BearResearchMemo, BullResearchMemo, ResearchTransition
from quantlab.agents.tool_contracts import AgentToolResult
from quantlab.agents.tool_gateway import AgentToolGateway
from quantlab.ai.permissions import DENIED_CAPABILITIES
from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.jobs import Job, JobStatus
from quantlab.realtime_data.service import inspect as inspect_snapshot
from quantlab.ui.widgets.agent_desk_webview import AgentDeskWebView
from quantlab.ui.widgets.analyst_workspace import AnalystWorkspace
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
        self._snapshot_path: Path | None = None
        self._history_path: Path | None = None
        self._job_id: str | None = None
        self._job_role = AgentRole.BULL
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
        self._bull = AnalystWorkspace()
        self._bull.historySelected.connect(lambda key: self._open_memo(key, AgentRole.BULL))
        self._tabs.addTab(self._bull, "Bull")
        self._inspectors["Bull"] = self._bull.memo
        self._bear = AnalystWorkspace(role=AgentRole.BEAR)
        self._bear.historySelected.connect(lambda key: self._open_memo(key, AgentRole.BEAR))
        self._tabs.addTab(self._bear, "Bear")
        self._inspectors["Bear"] = self._bear.memo
        self._workspaces = {AgentRole.BULL: self._bull, AgentRole.BEAR: self._bear}
        for name in ("Permissions", "Tools", "Audit"):
            inspector = QTextBrowser()
            inspector.setOpenExternalLinks(False)
            inspector.setAccessibleName(f"{name} research inspector")
            self._tabs.addTab(inspector, name)
            self._inspectors[name] = inspector
        self.body().addWidget(self._tabs, 1)
        refresh = QPushButton("Refresh desk status")
        refresh.clicked.connect(self.refresh)
        self.add_toolbar_widget(refresh)
        load_snapshot = QPushButton("Load snapshot")
        load_snapshot.clicked.connect(lambda: self._load_input(False))
        self.add_toolbar_widget(load_snapshot)
        load_history = QPushButton("Load PIT history")
        load_history.clicked.connect(lambda: self._load_input(True))
        self.add_toolbar_widget(load_history)
        self._replay = QCheckBox("Explicit replay")
        self._replay.setToolTip(
            "Historical/synthetic input remains clearly labelled; no live actions"
        )
        self.add_toolbar_widget(self._replay)
        self._run_button = QPushButton("Run Bull research")
        self._run_button.clicked.connect(self._run_bull)
        self.add_toolbar_widget(self._run_button)
        self._bear_button = QPushButton("Run Bear research")
        self._bear_button.clicked.connect(lambda: self._run_analyst(AgentRole.BEAR))
        self.add_toolbar_widget(self._bear_button)
        self._cancel_button = QPushButton("Cancel research")
        self._cancel_button.clicked.connect(self._cancel_bull)
        self._cancel_button.setEnabled(False)
        self.add_toolbar_widget(self._cancel_button)
        self._timer = QTimer(self)
        self._timer.setInterval(750)
        self._timer.timeout.connect(self.refresh)
        self.register_splitter(self._bull.main_splitter, "bull-workspace")
        self.register_splitter(self._bull.evidence_splitter, "bull-evidence")
        self.register_splitter(self._bear.main_splitter, "bear-workspace")
        self.register_splitter(self._bear.evidence_splitter, "bear-evidence")
        self.bind_splitter_preferences(layout_id="ai-quant-desk", settings=runtime.ui_settings)
        self.refresh()

    def _visual_navigation(self, intent: str, identity: str) -> None:
        if intent == "select_agent":
            self._tabs.setCurrentIndex(0 if identity == "BULL" else 1)
        elif intent == "open_evidence":
            try:
                repository = AgentRepository(self._repo_path)
                try:
                    result = repository.get(identity, AgentToolResult)
                    context = repository.get(result.context_hash, AgentRunContext)
                    workspace = self._workspaces[context.agent.role]
                    workspace.timeline.setPlainText(
                        json.dumps(result.model_dump(mode="json"), indent=2)
                    )
                    workspace.tabs.setCurrentIndex(2)
                    self._tabs.setCurrentWidget(workspace)
                finally:
                    repository.close()
            except (OSError, RuntimeError, ValueError, KeyError):
                self._bull.task.setText(
                    "Evidence unavailable; no replacement result was generated."
                )

    def _load_input(self, history: bool) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load frozen research input", "", "JSON (*.json)"
        )
        if not filename:
            return
        if history:
            self._history_path = Path(filename)
        else:
            self._snapshot_path = Path(filename)
        for workspace in self._workspaces.values():
            workspace.task.setText(
                "Input selected; scope, provenance and availability are checked on run."
            )

    def _run_bull(self) -> None:
        self._run_analyst(AgentRole.BULL)

    def _run_analyst(self, role: AgentRole) -> None:
        workspace = self._workspaces[role]
        self._tabs.setCurrentWidget(workspace)
        if self._job_id:
            workspace.task.setText(
                "A research job is already running. Cancel it before starting another."
            )
            return
        if not self._provider.health().configured:
            workspace.task.setText(
                "BLOCKED · configure OPENAI_API_KEY and QUANT_LAB_AGENT_MODEL "
                "locally in .env. Never paste credentials into this workspace."
            )
            return
        try:
            snapshot = (
                read_snapshot(self._snapshot_path) if self._snapshot_path else inspect_snapshot()
            )
            if snapshot is None:
                workspace.task.setText(
                    "BLOCKED · capture a market-data snapshot or load saved JSON. "
                    "No mock data is substituted automatically."
                )
                return
            now = datetime.now(UTC)
            history = (
                read_history(self._history_path, snapshot, now) if self._history_path else None
            )
            repository = AgentRepository(self._repo_path)
            try:
                factory = create_bull_context if role is AgentRole.BULL else create_bear_context
                context = factory(
                    repository,
                    snapshot,
                    self._provider,
                    now=now,
                    history=history,
                    mode=ResearchMode.REPLAY if self._replay.isChecked() else ResearchMode.RESEARCH,
                )
            finally:
                repository.close()
        except (OSError, RuntimeError, ValueError, KeyError):
            workspace.task.setText(
                "BLOCKED · invalid/stale input or persistence failure. "
                "Use Explicit replay only for intentional historical research."
            )
            return

        def work(job: Job) -> dict[str, object]:
            repo = AgentRepository(self._repo_path)
            try:
                worker = BullWorker if role is AgentRole.BULL else BearWorker
                record = worker(repo, self._provider).run(context, cancel=job.cancel_event)
                return {
                    "run_id": record.run_id,
                    "record_hash": record.content_hash,
                    "state": record.state.value,
                }
            finally:
                repo.close()

        job = self.runtime.jobs.submit(
            f"{role.value.lower()}_research", work, {"context_hash": context.content_hash}
        )
        self._job_id = job.job_id
        self._job_role = role
        self._run_button.setEnabled(False)
        self._bear_button.setEnabled(False)
        self._cancel_button.setEnabled(True)
        workspace.task.setText("Queued · frozen context verified · RESEARCH ONLY")
        self._timer.start()

    def _cancel_bull(self) -> None:
        if self._job_id:
            self.runtime.jobs.cancel(self._job_id)
            self._workspaces[self._job_role].task.setText(
                "Cancellation requested; late model responses cannot freeze a memo."
            )

    def _open_memo(self, memo_hash: str, role: AgentRole = AgentRole.BULL) -> None:
        repository: AgentRepository | None = None
        workspace = self._workspaces[role]
        try:
            repository = AgentRepository(self._repo_path)
            contract = BullResearchMemo if role is AgentRole.BULL else BearResearchMemo
            workspace.show_memo(repository.get(memo_hash, contract))
            workspace.tabs.setCurrentIndex(0)
        except (RuntimeError, ValueError, KeyError):
            workspace.task.setText("Saved memo could not be verified.")
        finally:
            if repository is not None:
                repository.close()

    def refresh(self) -> None:
        if self._job_id:
            job = self.runtime.jobs.get(self._job_id)
            if job is None or job.status in {
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
            }:
                self._job_id = None
                self._timer.stop()
                self._run_button.setEnabled(True)
                self._bear_button.setEnabled(True)
                self._cancel_button.setEnabled(False)
                if job and job.status is not JobStatus.COMPLETED:
                    self._workspaces[self._job_role].task.setText(
                        f"Research job {job.status}; inspect the persisted timeline."
                    )
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
                evidence: list[EvidenceNodeSummaryDTO] = []
                transitions = repository.list(ResearchTransition)
                for role, workspace in self._workspaces.items():
                    role_runs = []
                    for run in runs:
                        context = repository.get(run.context_hash, AgentRunContext)
                        if context.agent.role is role:
                            role_runs.append(run)
                    latest = role_runs[-1] if role_runs else None
                    states.append(presentation.from_run(role, latest))
                    if role in self._workspaces:
                        search = (
                            search_bull_history if role is AgentRole.BULL else search_bear_history
                        )
                        contract = BullResearchMemo if role is AgentRole.BULL else BearResearchMemo
                        memos = search(repository)
                        workspace.set_history(memos)
                        if latest and latest.memo_hash:
                            workspace.show_memo(repository.get(latest.memo_hash, contract))
                        if memos:
                            evidence.extend(
                                EvidenceNodeSummaryDTO(
                                    artifact_hash=row.result_hash,
                                    label=row.name,
                                    status=row.status,
                                )
                                for row in memos[-1].evidence_sections
                            )
                        analyst_transitions = [
                            row
                            for row in transitions
                            if repository.get(row.context_hash, AgentRunContext).agent.role is role
                        ]
                        if analyst_transitions:
                            active = analyst_transitions[-1]
                            active_tools = [
                                row
                                for row in repository.list(AgentToolResult)
                                if row.run_id == active.run_id
                            ]
                            workspace.task.setText(f"{active.state} · {active.task}")
                            workspace.timeline.setPlainText(
                                "\n".join(
                                    f"{row.sequence} · {row.state} · {row.task} · "
                                    f"{len(row.tool_result_hashes)} completed tools"
                                    for row in analyst_transitions
                                    if row.run_id == active.run_id
                                )
                                + "\n\nCANONICAL TOOL CALLS\n"
                                + "\n".join(
                                    f"{row.tool}: {row.status} · {row.error_code or 'completed'}\n"
                                    f"{row.content_hash}"
                                    for row in active_tools
                                )
                            )
                            states[-1] = AgentVisualStateDTO(
                                agent=role,
                                state=active.state,
                                task_label=active.task,
                                completed_tools=len(active_tools),
                                raw_confidence=(
                                    memos[-1].raw_confidence
                                    if memos and memos[-1].context_hash == active.context_hash
                                    else None
                                ),
                            )
                        continue
                mandate = bull_mandate(datetime(2026, 10, 4, tzinfo=UTC))
                self._inspectors["Permissions"].setPlainText(
                    json.dumps(
                        {
                            "allowed": sorted(mandate.granted),
                            "bear_allowed": sorted(bear_mandate(mandate.created_at).granted),
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
                self._visual.bridge.publish(tuple(states), tuple(evidence))
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
