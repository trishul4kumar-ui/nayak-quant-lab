from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from quantlab.agents.contracts import AgentRole, AgentState
from quantlab.agents.presentation import AgentVisualStateDTO, EvidenceNodeSummaryDTO
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
