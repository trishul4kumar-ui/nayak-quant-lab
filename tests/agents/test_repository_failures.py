from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication
from tests.agents.conftest import NOW

from quantlab.agents.cli import run_agents_command
from quantlab.agents.hashing import Artifact
from quantlab.agents.repository import AgentRepository
from quantlab.app.bootstrap import bootstrap
from quantlab.control_plane.sqlite import ControlPlaneStoreError
from quantlab.ui.pages.ai_quant_desk import AiQuantDeskPage


def test_corrupt_repository_rejects_without_overwriting(tmp_path: Path) -> None:
    path = tmp_path / "broken.sqlite"
    original = b"not a database; sensitive local information"
    path.write_bytes(original)
    with pytest.raises(ControlPlaneStoreError, match="^AGENT_PERSISTENCE_UNAVAILABLE$"):
        AgentRepository(path)
    assert path.read_bytes() == original


def test_closed_repository_reads_and_writes_fail_safely(tmp_path: Path) -> None:
    repo = AgentRepository(tmp_path / "closed.sqlite")
    artifact = repo.put(Artifact(created_at=NOW))
    repo.close()
    repo.close()
    for operation in (
        lambda: repo.get(artifact.content_hash, Artifact),
        lambda: repo.list(Artifact),
        repo.audit_events,
        lambda: repo.put(artifact),
    ):
        with pytest.raises(ControlPlaneStoreError, match="^AGENT_PERSISTENCE_UNAVAILABLE$"):
            operation()


def test_cli_persistence_error_is_safe_json(capsys: pytest.CaptureFixture[str]) -> None:
    with patch(
        "quantlab.agents.cli.AgentRepository",
        side_effect=ControlPlaneStoreError("private local details"),
    ):
        result = run_agents_command(argparse.Namespace(agents_action="status", run_id=None))
    payload = json.loads(capsys.readouterr().out)
    assert result == 2
    assert payload == {"error": "AGENT_PERSISTENCE_UNAVAILABLE", "live_trading": False}


def test_corrupt_desk_does_not_crash_native_application(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    runtime = bootstrap(data_dir=tmp_path)
    path = runtime.paths.database_dir / "agent_desk.sqlite"
    path.write_bytes(b"not a database")
    page = AiQuantDeskPage(runtime)
    try:
        page.show()
        app.processEvents()
        assert "DESK BLOCKED" in page._status.text()
        assert all("blocked" in row.toPlainText() for row in page._inspectors.values())
        presentation = json.loads(page._visual.bridge.presentation)
        assert {row["state"] for row in presentation["agents"]} == {"BLOCKED"}
        assert not presentation["safety"]["ai_order_authority"]
        page.refresh()
        assert path.read_bytes() == b"not a database"
    finally:
        page.close()
        runtime.shutdown()
