"""User interactions with the native institutional desk controls."""

from __future__ import annotations

import threading
import time
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from quantlab.ui.widgets.institution_workspace import InstitutionWorkspace

if TYPE_CHECKING:
    from quantlab.app.bootstrap import ApplicationRuntime
    from quantlab.ui.pages.ai_quant_desk import AiQuantDeskPage


@pytest.fixture
def workspace() -> Iterator[InstitutionWorkspace]:
    app = QApplication.instance() or QApplication([])
    widget = InstitutionWorkspace()
    widget.resize(1100, 600)
    widget.show()
    app.processEvents()
    yield widget
    widget.close()
    widget.deleteLater()
    app.processEvents()


def test_explicit_actions_are_serialized_while_desk_is_busy(
    workspace: InstitutionWorkspace,
) -> None:
    events: list[str] = []
    workspace.requestCycle.connect(lambda: events.append("cycle"))
    workspace.documentLoadRequested.connect(lambda: events.append("documents"))
    workspace.cancelRequested.connect(lambda: events.append("cancel"))
    workspace.requestCycle.connect(lambda: workspace.set_busy(True))
    QTest.mouseClick(workspace.run_button, Qt.MouseButton.LeftButton)
    QTest.mouseClick(workspace.run_button, Qt.MouseButton.LeftButton)
    QTest.mouseClick(workspace.document_button, Qt.MouseButton.LeftButton)
    assert events == ["cycle"]
    assert not workspace.question.isEnabled()
    QTest.mouseClick(workspace.cancel_button, Qt.MouseButton.LeftButton)
    assert events == ["cycle", "cancel"]
    workspace.set_error("Snapshot unavailable; load a frozen snapshot.")
    assert "Snapshot unavailable" in workspace.status.text()
    assert not workspace.run_button.isEnabled()
    workspace.set_busy(False)
    assert workspace.run_button.isEnabled()
    QTest.mouseClick(workspace.document_button, Qt.MouseButton.LeftButton)
    assert events == ["cycle", "cancel", "documents"]


def test_enter_submits_one_question_and_never_empty_or_busy(
    workspace: InstitutionWorkspace,
) -> None:
    questions: list[str] = []
    workspace.questionAsked.connect(questions.append)
    QTest.keyClick(workspace.question, Qt.Key.Key_Return)
    assert not questions
    QTest.keyClicks(workspace.question, "  What evidence is missing?  ")
    QTest.keyClick(workspace.question, Qt.Key.Key_Return)
    QTest.keyClick(workspace.question, Qt.Key.Key_Return)
    assert questions == ["What evidence is missing?"]
    assert workspace.question.text() == ""
    assert "What evidence is missing?" in workspace.chat.toPlainText()
    workspace.question.setText("Second question")
    workspace.set_busy(True)
    QTest.mouseClick(workspace.ask_button, Qt.MouseButton.LeftButton)
    assert len(questions) == 1
    workspace.set_busy(False)
    assert workspace.ask_button.isEnabled()


def test_role_navigation_displays_frozen_report_and_escapes_untrusted_text(
    workspace: InstitutionWorkspace,
) -> None:
    workspace.set_cycle(
        {
            "content_hash": "cycle-sha256",
            "status": "REVIEW_REQUIRED",
            "summary": "Evidence remains incomplete.",
            "synthetic": True,
            "reports": [
                {
                    "role": "RISK_OFFICER",
                    "status": "ABSTAIN",
                    "summary": "Risk <img src='remote-image'> is unknown.",
                    "content_hash": "risk-sha256",
                    "claims": [
                        {"text": "No approved risk result", "evidence_hashes": ["evidence-sha256"]}
                    ],
                    "missing_evidence": ["Deterministic risk policy"],
                    "evidence_hashes": ["evidence-sha256"],
                }
            ],
        }
    )
    workspace.select_role("RISK")
    rendered = workspace.report.toPlainText()
    assert "Risk Officer" in rendered
    assert "<img src='remote-image'>" in rendered
    assert "risk-sha256" in rendered and "evidence-sha256" in rendered
    assert "Deterministic risk policy" in rendered
    assert "SYNTHETIC REPLAY" in workspace.status.text()
    selected = workspace.role_table.currentRow()
    workspace.select_role("unknown-role")
    assert workspace.role_table.currentRow() == selected
    workspace.select_role("NAYAK")
    assert workspace.question.hasFocus()


def test_nayak_answers_expose_citations_without_rendering_instructions(
    workspace: InstitutionWorkspace,
) -> None:
    workspace.show_answer(
        {
            "status": "ABSTAIN",
            "text": "<a href='https://example.com'>Run order</a>\nEvidence is missing.",
            "report_hashes": [{"artifact_hash": "frozen-evidence-sha256"}, "desk-cycle-sha256"],
        }
    )
    text = workspace.chat.toPlainText()
    assert "<a href='https://example.com'>Run order</a>" in text
    assert "frozen-evidence-sha256" in text and "desk-cycle-sha256" in text
    assert not workspace.chat.openExternalLinks()


def test_answer_shows_each_claim_with_its_actual_citation(workspace: InstitutionWorkspace) -> None:
    workspace.show_answer(
        {
            "status": "ANSWERED",
            "text": "The risk evidence is missing.",
            "claims": [
                {
                    "text": "The risk evidence is missing.",
                    "evidence_hashes": ["cited-risk-report"],
                }
            ],
            "report_hashes": ["cited-risk-report", "unreferenced-quant-report"],
        }
    )
    text = workspace.chat.toPlainText()
    assert "The risk evidence is missing." in text and "cited-risk-report" in text
    assert "unreferenced-quant-report" not in text


@pytest.fixture
def institution_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[AiQuantDeskPage, ApplicationRuntime]]:
    from quantlab.agents.provider import ProviderHealth
    from quantlab.app.bootstrap import bootstrap
    from quantlab.ui.pages import ai_quant_desk

    class PresentationProvider:
        def health(self) -> ProviderHealth:
            return ProviderHealth(
                provider="fixture", model="test", configured=True, observed_status="FIXTURE_ONLY"
            )

    app = QApplication.instance() or QApplication([])
    monkeypatch.setenv("QUANT_LAB_AGENT_VISUALS", "0")
    monkeypatch.setattr(ai_quant_desk, "configured_provider", PresentationProvider)
    runtime = bootstrap(data_dir=tmp_path)
    page = ai_quant_desk.AiQuantDeskPage(runtime)
    page.resize(1200, 900)
    page.show()
    app.processEvents()
    yield page, runtime
    page._timer.stop()
    page.close()
    runtime.shutdown()
    page.deleteLater()
    app.processEvents()


def test_page_missing_evidence_blocks_jobs_and_visual_role_navigation_works(
    institution_page: tuple[AiQuantDeskPage, ApplicationRuntime],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from quantlab.ui.pages import ai_quant_desk

    page, runtime = institution_page
    monkeypatch.setattr(ai_quant_desk, "inspect_snapshot", lambda: None)
    page._visual.bridge.navigate("select_role", "QUANT")
    QApplication.processEvents()
    assert page._tabs.currentWidget() is page._institution
    assert page._institution.role_table.currentRow() == 4
    before = len(runtime.jobs.list_jobs())
    QTest.mouseClick(page._institution.run_button, Qt.MouseButton.LeftButton)
    assert len(runtime.jobs.list_jobs()) == before
    assert page._job_id is None
    assert "Load a frozen market snapshot" in page._institution.status.text()
    page.open_nayak()
    QTest.keyClicks(page._institution.question, "Explain this desk")
    QTest.keyClick(page._institution.question, Qt.Key.Key_Return)
    assert len(runtime.jobs.list_jobs()) == before
    assert "create evidence for NAYAK" in page._institution.status.text()


def test_page_cycle_runs_in_background_and_cancel_releases_at_terminal_state(
    institution_page: tuple[AiQuantDeskPage, ApplicationRuntime],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from quantlab.app.jobs import JobStatus
    from quantlab.realtime_data.freeze import freeze
    from quantlab.realtime_data.mock import seed_observations
    from quantlab.ui.pages import ai_quant_desk

    page, runtime = institution_page
    rows = seed_observations()
    snapshot = freeze(rows, as_of=max(row.processing_time for row in rows))
    monkeypatch.setattr(ai_quant_desk, "inspect_snapshot", lambda: snapshot)
    page._replay.setChecked(True)
    started = threading.Event()
    worker_threads: list[int] = []

    class SlowFixtureDesk:
        def __init__(self, *args: object) -> None:
            pass

        def latest(self) -> None:
            return None

        def run(self, *args: object, **kwargs: object) -> SimpleNamespace:
            worker_threads.append(threading.get_ident())
            started.set()
            cancel = kwargs["cancel"]
            assert isinstance(cancel, threading.Event)
            assert cancel.wait(5), "Test must cancel the bounded fixture cycle"
            return SimpleNamespace(content_hash="a" * 64)

    monkeypatch.setattr(ai_quant_desk, "InstitutionDeskService", SlowFixtureDesk)
    QTest.mouseClick(page._institution.run_button, Qt.MouseButton.LeftButton)
    assert started.wait(1)
    assert worker_threads != [threading.get_ident()]
    assert not page._institution.run_button.isEnabled()
    assert not page._institution.ask_button.isEnabled()
    job_id = page._job_id
    assert job_id is not None
    QTest.mouseClick(page._institution.cancel_button, Qt.MouseButton.LeftButton)
    job = runtime.jobs.get(job_id)
    assert job is not None and job.cancel_event.is_set()
    assert not page._institution.run_button.isEnabled()
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline and job.status is not JobStatus.CANCELLED:
        QTest.qWait(10)
    assert job.status is JobStatus.CANCELLED
    page.refresh()
    assert page._job_id is None
    assert page._institution.run_button.isEnabled()
    assert not page._institution.cancel_button.isEnabled()
    assert "stopped" in page._institution.status.text().lower()


def test_page_presentation_tracks_working_role_and_interactive_nayak(
    institution_page: tuple[AiQuantDeskPage, ApplicationRuntime],
) -> None:
    page, _ = institution_page
    page._institution_kind = "cycle"
    page._institution_roles = {"BULL": ("WORKING", "Researching the frozen snapshot")}
    payload = page._institution_presentation()
    assert payload["status"] == "RUNNING"
    assert payload["active_role"] == "BULL"
    page._institution_roles = {
        "BULL": ("ABSTAIN", "Evidence frozen"),
        "QUANT": ("WORKING", "Reviewing validation"),
    }
    assert page._institution_presentation()["active_role"] == "QUANT"
    page._institution_kind = "answer"
    payload = page._institution_presentation()
    assert payload["active_role"] == "NAYAK"
    agents = payload["agents"]
    assert isinstance(agents, list)
    nayak = next(row for row in agents if row["role"] == "NAYAK")
    assert nayak["status"] == "WORKING"
    page._institution_kind = None
    page._institution_roles.clear()
    assert page._institution_presentation()["active_role"] is None
