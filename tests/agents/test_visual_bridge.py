from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from quantlab.agents.contracts import AgentRole, AgentState
from quantlab.agents.debate_contracts import DebateStatus, EvidenceRelation
from quantlab.agents.presentation import (
    AdjudicationVisualDTO,
    AgentVisualStateDTO,
    DebateVisualDTO,
    EvidenceEdgeDTO,
    EvidenceNodeSummaryDTO,
)
from quantlab.ui.widgets.agent_desk_webview import AgentDeskWebView


@pytest.fixture
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_native_fallback_and_bridge_only_navigates(qapp: QApplication) -> None:
    view = AgentDeskWebView()
    assert view._web is None
    observed: list[tuple[str, str]] = []
    view.bridge.navigationRequested.connect(
        lambda intent, identity: observed.append((intent, identity))
    )
    view.bridge.navigate("place_order", "anything")
    view.bridge.navigate("open_evidence", "f" * 64)
    assert not observed
    view.bridge.publish(
        (
            AgentVisualStateDTO(
                agent=AgentRole.BULL,
                state=AgentState.IDLE,
                task_label="Research",
                completed_tools=0,
            ),
        ),
        (EvidenceNodeSummaryDTO(artifact_hash="f" * 64, label="evidence", status="PASS"),),
    )
    view.bridge.navigate("open_evidence", "f" * 64)
    assert observed == [("open_evidence", "f" * 64)]
    assert not hasattr(view.bridge, "submit")
    assert not hasattr(view.bridge, "execute")
    view.close()


def test_adjudication_bridge_only_opens_published_decision(qapp: QApplication) -> None:
    from quantlab.agents.adjudication_contracts import AdjudicationOutcome

    view = AgentDeskWebView()
    observed = []
    view.bridge.navigationRequested.connect(lambda *args: observed.append(args))
    view.bridge.navigate("open_adjudication", "d" * 64)
    assert not observed
    view.bridge.publish(
        (),
        (),
        None,
        AdjudicationVisualDTO(
            decision_hash="d" * 64,
            transcript_hash="a" * 64,
            outcome=AdjudicationOutcome.INSUFFICIENT_DATA,
            no_trade=True,
            bull_score=0,
            bear_score=0,
            blocker_count=40,
            expired=True,
            components=(),
            warnings=("Missing canonical evidence",),
        ),
    )
    view.bridge.navigate("open_adjudication", "c" * 64)
    view.bridge.navigate("execute_decision", "d" * 64)
    assert not observed
    view.bridge.navigate("open_adjudication", "d" * 64)
    assert observed == [("open_adjudication", "d" * 64)]
    view.bridge.publish((), ())
    view.bridge.navigate("open_adjudication", "d" * 64)
    assert len(observed) == 1
    view.close()


def test_debate_bridge_only_opens_published_transcript(qapp: QApplication) -> None:
    view = AgentDeskWebView()
    observed = []
    view.bridge.navigationRequested.connect(lambda *args: observed.append(args))
    view.bridge.navigate("open_debate", "a" * 64)
    assert not observed
    view.bridge.publish(
        (),
        (EvidenceNodeSummaryDTO(artifact_hash="b" * 64, label="canonical", status="NOT_TESTED"),),
        DebateVisualDTO(
            transcript_hash="a" * 64,
            status=DebateStatus.INCOMPLETE,
            critiques=0,
            rebuttals=0,
            edges=(
                EvidenceEdgeDTO(
                    agent=AgentRole.BULL, evidence_hash="b" * 64, relation=EvidenceRelation.SUPPORT
                ),
            ),
        ),
    )
    view.bridge.navigate("open_debate", "c" * 64)
    view.bridge.navigate("place_live_order", "a" * 64)
    assert not observed
    view.bridge.navigate("open_debate", "a" * 64)
    assert observed == [("open_debate", "a" * 64)]
    view.close()
