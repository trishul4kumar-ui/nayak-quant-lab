from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest
from tests.agents.test_bull import ResearchFixtureProvider, snapshot

from quantlab.agents.cli import add_agents_parser, run_agents_command
from quantlab.agents.inputs import read_snapshot
from quantlab.agents.provider import UnavailableProvider, configured_provider
from quantlab.agents.repository import AgentRepository


def test_explicit_dotenv_model_configuration_keeps_secret_private(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("QUANT_LAB_AGENT_MODEL", raising=False)
    assert not configured_provider().health().configured
    key_name = "_".join(("OPENAI", "API", "KEY"))
    fixture = "configuration-fixture-not-a-real-credential"
    (tmp_path / ".env").write_text(f"{key_name}={fixture}\nQUANT_LAB_AGENT_MODEL=explicit-model\n")
    provider = configured_provider()
    health = provider.health().model_dump(mode="json")
    assert health["configured"] is True and health["observed_status"] == "NOT_TESTED"
    assert health["model"] == "explicit-model"
    assert fixture not in json.dumps(health)


def test_import_size_limit_blocks_before_reading(tmp_path: Path) -> None:
    target = tmp_path / "too-large.json"
    target.write_bytes(b" " * 4_000_001)
    with pytest.raises(ValueError, match="TOO_LARGE"):
        read_snapshot(target)


def test_cli_runs_and_searches_frozen_bull_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    saved = tmp_path / "snapshot.json"
    saved.write_text(snapshot().model_dump_json())
    provider = ResearchFixtureProvider("NO_TRADE")
    monkeypatch.setattr("quantlab.agents.cli.configured_provider", lambda: provider)
    monkeypatch.setattr(
        "quantlab.agents.cli.AgentRepository", lambda: AgentRepository(tmp_path / "cli.sqlite")
    )
    parser = argparse.ArgumentParser()
    add_agents_parser(parser.add_subparsers())
    args = parser.parse_args(["agents", "run-bull", "--snapshot", str(saved), "--replay"])
    assert run_agents_command(args) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "NO_TRADE"
    args = parser.parse_args(["agents", "bull-history", "--query", "empirical"])
    assert run_agents_command(args) == 0
    history = json.loads(capsys.readouterr().out)
    assert len(history) == 1 and history[0]["validation"] == "NOT_TESTED"
    assert provider.calls == 2


def test_cli_blocked_research_has_nonzero_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    saved = tmp_path / "snapshot.json"
    saved.write_text(snapshot().model_dump_json())
    monkeypatch.setattr("quantlab.agents.cli.configured_provider", UnavailableProvider)
    monkeypatch.setattr(
        "quantlab.agents.cli.AgentRepository", lambda: AgentRepository(tmp_path / "cli.sqlite")
    )
    parser = argparse.ArgumentParser()
    add_agents_parser(parser.add_subparsers())
    args = parser.parse_args(["agents", "run-bull", "--snapshot", str(saved), "--replay"])
    assert run_agents_command(args) == 2
    assert json.loads(capsys.readouterr().out)["state"] == "BLOCKED"
