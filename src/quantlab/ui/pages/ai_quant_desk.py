"""Native, accessible entry point for the research-only agent foundation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from quantlab.agents.adjudication_contracts import AdjudicationDecision, FrozenAdjudicationInput
from quantlab.agents.adjudication_service import run_adjudication, verify_adjudication
from quantlab.agents.bear import BearWorker, bear_mandate, create_bear_context, search_bear_history
from quantlab.agents.bull import BullWorker, bull_mandate, create_bull_context, search_bull_history
from quantlab.agents.contracts import (
    AgentRole,
    AgentRunContext,
    AgentRunRecord,
    AgentState,
    ResearchMode,
)
from quantlab.agents.debate import DebateWorker, create_debate, verify_transcript
from quantlab.agents.debate_contracts import DebateTranscript, FrozenCritique, FrozenRebuttal
from quantlab.agents.inputs import read_history, read_snapshot
from quantlab.agents.presentation import (
    AdjudicationVisualDTO,
    AgentDeskPresentationService,
    AgentVisualStateDTO,
    ComponentVisualDTO,
    DebateVisualDTO,
    EvidenceEdgeDTO,
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
from quantlab.ui.widgets.adjudication_workspace import AdjudicationWorkspace
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
        self._debate_job = False
        self._active_debate_id: str | None = None
        self._selected_debate: str | None = None
        self._selected_decision: str | None = None
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
        self._debate = QWidget()
        debate_layout = QVBoxLayout(self._debate)
        self._debate_status = QLabel("Freeze both independent initials before starting a debate.")
        self._debate_status.setWordWrap(True)
        debate_layout.addWidget(self._debate_status)
        controls = QHBoxLayout()
        self._debate_button = QPushButton("Debate latest frozen memos")
        self._debate_button.clicked.connect(self._run_debate)
        self._rebuttals = QCheckBox("One optional rebuttal each")
        self._rebuttals.setToolTip("Adds two bounded model calls; never recursive")
        self._debate_choice = QComboBox()
        self._debate_choice.setAccessibleName("Saved immutable debate transcripts")
        self._debate_choice.currentIndexChanged.connect(self._choose_debate)
        controls.addWidget(self._debate_button)
        controls.addWidget(self._rebuttals)
        controls.addWidget(self._debate_choice, 1)
        debate_layout.addLayout(controls)
        debate_splitter = QSplitter(Qt.Orientation.Vertical)
        self._transcript = QTextBrowser()
        self._transcript.setOpenExternalLinks(False)
        self._transcript.setAccessibleName("Native immutable debate transcript")
        self._transcript.setPlainText("No debate transcripts yet. No opposing view is fabricated.")
        self._falsification = QTextBrowser()
        self._falsification.setAccessibleName("Canonical falsification checks and evidence gaps")
        debate_splitter.addWidget(self._transcript)
        debate_splitter.addWidget(self._falsification)
        debate_splitter.setChildrenCollapsible(False)
        debate_splitter.setSizes([360, 180])
        debate_layout.addWidget(debate_splitter, 1)
        self._tabs.addTab(self._debate, "Debate Arena")
        self._inspectors["Debate"] = self._transcript
        self._adjudication = AdjudicationWorkspace()
        self._adjudication.run_button.clicked.connect(self._run_adjudication)
        self._adjudication.history.currentIndexChanged.connect(self._choose_adjudication)
        self._tabs.addTab(self._adjudication, "Adjudication")
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
        self.register_splitter(debate_splitter, "debate-workspace")
        self.register_splitter(self._adjudication.splitter, "adjudication-workspace")
        self.bind_splitter_preferences(layout_id="ai-quant-desk", settings=runtime.ui_settings)
        self.refresh()

    def _visual_navigation(self, intent: str, identity: str) -> None:
        if intent == "select_agent":
            self._tabs.setCurrentIndex(0 if identity == "BULL" else 1)
        elif intent == "open_debate":
            self._selected_debate = identity
            self._tabs.setCurrentWidget(self._debate)
            self.refresh()
        elif intent == "open_adjudication":
            self._selected_decision = identity
            self._tabs.setCurrentWidget(self._adjudication)
            self.refresh()
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
        self._debate_job = False
        self._job_role = role
        self._run_button.setEnabled(False)
        self._bear_button.setEnabled(False)
        self._debate_button.setEnabled(False)
        self._cancel_button.setEnabled(True)
        workspace.task.setText("Queued · frozen context verified · RESEARCH ONLY")
        self._timer.start()

    def _cancel_bull(self) -> None:
        if self._job_id:
            self.runtime.jobs.cancel(self._job_id)
            if self._debate_job:
                self._debate_status.setText("Cancellation requested; no fabricated completion.")
                return
            self._workspaces[self._job_role].task.setText(
                "Cancellation requested; late model responses cannot freeze a memo."
            )

    def _run_debate(self) -> None:
        self._tabs.setCurrentWidget(self._debate)
        if self._job_id:
            self._debate_status.setText("BLOCKED · another desk job is running.")
            return
        repository: AgentRepository | None = None
        try:
            repository = AgentRepository(self._repo_path)
            bulls, bears = search_bull_history(repository), search_bear_history(repository)
            if not bulls or not bears:
                self._debate_status.setText("BLOCKED · freeze both real analyst memos first.")
                return
            session = create_debate(
                repository,
                bulls[-1].content_hash,
                bears[-1].content_hash,
                now=datetime.now(UTC),
                include_rebuttals=self._rebuttals.isChecked(),
            )
        except (OSError, RuntimeError, ValueError, KeyError):
            self._debate_status.setText(
                "BLOCKED · initials must share healthy, unexpired frozen snapshot and PIT history. "
                "Load the same saved inputs for both; no peer view is substituted."
            )
            return
        finally:
            if repository is not None:
                repository.close()

        def work(job: Job) -> dict[str, object]:
            repo = AgentRepository(self._repo_path)
            try:
                transcript = DebateWorker(repo, {role: self._provider for role in AgentRole}).run(
                    session, cancel=job.cancel_event
                )
                return {
                    "transcript_hash": transcript.content_hash,
                    "status": transcript.status.value,
                }
            finally:
                repo.close()

        job = self.runtime.jobs.submit("agent_debate", work, {"session_hash": session.content_hash})
        self._job_id, self._debate_job = job.job_id, True
        self._active_debate_id, self._selected_debate = session.debate_id, None
        for button in (self._run_button, self._bear_button, self._debate_button):
            button.setEnabled(False)
        self._cancel_button.setEnabled(True)
        self._debate_status.setText("Queued · both initials frozen · bounded critique only")
        self._timer.start()

    def _choose_debate(self, _: int) -> None:
        identity = self._debate_choice.currentData()
        if isinstance(identity, str):
            self._selected_debate = identity
            self._selected_decision = None
            self.refresh()

    def _run_adjudication(self) -> None:
        self._tabs.setCurrentWidget(self._adjudication)
        if self._job_id:
            self._adjudication.summary.setText("BLOCKED · finish or cancel the active research job")
            return
        identity = self._debate_choice.currentData()
        if not isinstance(identity, str):
            self._adjudication.summary.setText("BLOCKED · select a frozen debate transcript first")
            return
        repository = None
        try:
            repository = AgentRepository(self._repo_path)
            decision = run_adjudication(repository, identity, now=datetime.now(UTC))
            self._selected_decision = decision.content_hash
            self.refresh()
        except (OSError, RuntimeError, ValueError, KeyError):
            self._adjudication.summary.setText(
                "BLOCKED · evidence or persistence could not be verified"
            )
            self._adjudication.components.clear()
            self._adjudication.details.clear()
        finally:
            if repository:
                repository.close()

    def _choose_adjudication(self, _: int) -> None:
        identity = self._adjudication.history.currentData()
        if isinstance(identity, str):
            self._selected_decision = identity
            self.refresh()

    def _refresh_adjudication(
        self, repository: AgentRepository, transcript: DebateTranscript | None
    ) -> AdjudicationVisualDTO | None:
        choices = repository.list(AdjudicationDecision)[-100:]
        if transcript:
            choices = tuple(
                row for row in choices if row.transcript_hash == transcript.content_hash
            )
        self._adjudication.history.blockSignals(True)
        self._adjudication.history.clear()
        for row in choices:
            self._adjudication.history.addItem(
                f"{row.outcome} · {row.content_hash[:8]}", row.content_hash
            )
        selected = next(
            (row for row in choices if row.content_hash == self._selected_decision),
            choices[-1] if choices else None,
        )
        dto = None
        if selected:
            verify_adjudication(repository, selected)
            frame = repository.get(selected.input_hash, FrozenAdjudicationInput)
            current = datetime.now(UTC)
            expired = current >= frame.expires_at or (
                frame.mode is not ResearchMode.REPLAY
                and (current - frame.as_of).total_seconds() > 300
            )
            self._adjudication.history.setCurrentIndex(
                self._adjudication.history.findData(selected.content_hash)
            )
            self._adjudication.display(selected, expired=expired)
            dto = AdjudicationVisualDTO(
                decision_hash=selected.content_hash,
                transcript_hash=selected.transcript_hash,
                outcome=selected.outcome,
                no_trade=selected.no_trade,
                bull_score=selected.bull_score,
                bear_score=selected.bear_score,
                blocker_count=len(selected.hard_blockers),
                expired=expired,
                components=tuple(
                    ComponentVisualDTO(
                        role=row.role,
                        name=row.name,
                        status=row.status,
                        value=row.normalized_value,
                        points=row.points,
                    )
                    for row in selected.score_components
                ),
                warnings=selected.warnings,
            )
        else:
            self._adjudication.summary.setText("No adjudication for selected transcript · NO_TRADE")
            self._adjudication.components.clear()
            self._adjudication.details.clear()
        self._adjudication.history.blockSignals(False)
        return dto

    def _show_transcript(self, repository: AgentRepository, transcript: DebateTranscript) -> None:
        verify_transcript(repository, transcript)
        bull = repository.get(transcript.bull_memo_hash, BullResearchMemo)
        self._debate_status.setText(
            f"{bull.data_kind} · {transcript.status} · {len(transcript.critiques)} critiques / "
            f"{len(transcript.rebuttals)} rebuttals · NO EXECUTION AUTHORITY · "
            f"{transcript.error_code or 'Adjudication not built yet'}"
        )
        text = [
            f"Snapshot: {transcript.snapshot_hash}\nTranscript: {transcript.content_hash}\n"
            f"Started: {transcript.started_at.isoformat()}\n"
            f"Completed: {transcript.completed_at.isoformat()}\n"
            "Arguments and raw confidence are not quantitative evidence.\n"
        ]
        for key in transcript.critiques:
            critique = repository.get(key, FrozenCritique)
            text.append(
                f"\n{critique.draft.critic_agent} CRITIQUE · {key}\n"
                + json.dumps(critique.draft.model_dump(mode="json"), indent=2)
            )
        for key in transcript.rebuttals:
            rebuttal = repository.get(key, FrozenRebuttal)
            text.append(
                f"\n{rebuttal.draft.respondent_agent} FINAL REBUTTAL · {key}\n"
                + json.dumps(rebuttal.draft.model_dump(mode="json"), indent=2)
            )
        self._transcript.setPlainText("\n".join(text))
        self._falsification.setPlainText(
            "CANONICAL FALSIFICATION · exact named checks only\n\n"
            + "\n\n".join(
                f"{check.name}: {check.status}\n{check.note}"
                for check in transcript.falsification_checks
            )
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
                self._debate_button.setEnabled(True)
                self._cancel_button.setEnabled(False)
                if job and job.status is not JobStatus.COMPLETED:
                    if self._debate_job:
                        self._debate_status.setText(
                            f"Debate job {job.status}; no completion fabricated."
                        )
                    else:
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
                transcripts = repository.list(DebateTranscript)[-100:]
                self._debate_choice.blockSignals(True)
                self._debate_choice.clear()
                for row in transcripts:
                    self._debate_choice.addItem(
                        f"{row.status} · {row.debate_id[-8:]}", row.content_hash
                    )
                selected = next(
                    (row for row in transcripts if row.content_hash == self._selected_debate),
                    transcripts[-1] if transcripts else None,
                )
                debate_dto = None
                if selected:
                    self._debate_choice.setCurrentIndex(
                        self._debate_choice.findData(selected.content_hash)
                    )
                    self._show_transcript(repository, selected)
                    evidence = [
                        EvidenceNodeSummaryDTO(
                            artifact_hash=key, label=result.tool.value, status=result.status
                        )
                        for key in selected.evidence_hashes
                        for result in (repository.get(key, AgentToolResult),)
                    ]
                    debate_dto = DebateVisualDTO(
                        transcript_hash=selected.content_hash,
                        status=selected.status,
                        critiques=len(selected.critiques),
                        rebuttals=len(selected.rebuttals),
                        edges=tuple(
                            EvidenceEdgeDTO(
                                agent=edge.agent,
                                evidence_hash=edge.evidence_hash,
                                relation=edge.relation,
                            )
                            for edge in selected.evidence_graph[:80]
                        ),
                    )
                self._debate_choice.blockSignals(False)
                if self._job_id and self._debate_job:
                    events = repository.audit_events(self._active_debate_id)
                    active_event = next(
                        (
                            event
                            for event in reversed(events)
                            if event.event in {"DEBATE_CRITIQUING", "DEBATE_REBUTTING"}
                        ),
                        None,
                    )
                    if active_event and active_event.safe_code in {
                        role.value for role in AgentRole
                    }:
                        role = AgentRole(active_event.safe_code)
                        self._debate_status.setText(
                            f"{active_event.event} · {role} · bounded protocol active"
                        )
                        states = [
                            AgentVisualStateDTO(
                                agent=state.agent,
                                state=AgentState.CRITIQUING
                                if active_event.event == "DEBATE_CRITIQUING"
                                else AgentState.REBUTTING,
                                task_label=active_event.event,
                                completed_tools=state.completed_tools,
                            )
                            if state.agent is role
                            else state
                            for state in states
                        ]
                decision_dto = self._refresh_adjudication(repository, selected)
                self._visual.bridge.publish(
                    tuple(states), tuple(evidence[:40]), debate_dto, decision_dto
                )
            finally:
                repository.close()
        except (OSError, RuntimeError, ValueError, KeyError):
            self._status.setText("DESK BLOCKED · research persistence could not be verified")
            self._debate_status.setText("BLOCKED · saved transcript could not be verified")
            self._debate_choice.blockSignals(True)
            self._debate_choice.clear()
            self._debate_choice.blockSignals(False)
            self._falsification.clear()
            self._adjudication.summary.setText("BLOCKED · saved adjudication could not be verified")
            self._adjudication.components.clear()
            self._adjudication.details.clear()
            self._adjudication.history.blockSignals(True)
            self._adjudication.history.clear()
            self._adjudication.history.blockSignals(False)
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
