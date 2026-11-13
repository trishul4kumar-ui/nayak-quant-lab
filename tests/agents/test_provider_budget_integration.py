from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest
from tests.app.test_strategy_research import ProposalProvider, execute

from quantlab.agents.budget_scopes import strategy_research_family
from quantlab.agents.cli import add_agents_parser, run_agents_command
from quantlab.agents.errors import AgentProviderError
from quantlab.agents.provider_budget import ProviderBudgetLedger, ProviderBudgetPolicy
from quantlab.agents.repository import AgentRepository


def test_strategy_family_rejects_non_instrument_text() -> None:
    assert strategy_research_family("NSE:INFY") == "strategy:NSE:INFY"
    for invalid in ("NSE:INFY secret", "nse:INFY", "NSE:" + "A" * 81):
        with pytest.raises(ValueError, match="INVALID_STRATEGY_BUDGET_INSTRUMENT"):
            strategy_research_family(invalid)


def test_strategy_batches_share_durable_family_budget(tmp_path: Path) -> None:
    repo = AgentRepository(tmp_path / "agents.sqlite")
    ProviderBudgetLedger(repo).configure(ProviderBudgetPolicy(6000, 9000, 50000))
    repo.close()
    provider = ProposalProvider()
    execute(tmp_path, provider)
    with pytest.raises(AgentProviderError, match="FAMILY_EXCEEDED"):
        execute(tmp_path, provider)
    assert len(provider.requests) == 1
    assert provider.requests[0].budget_family_id == "strategy:NSE:INFY"


def test_owner_cli_status_configuration_and_immutable_conflict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "agents.sqlite"
    monkeypatch.setattr("quantlab.agents.cli.AgentRepository", lambda: AgentRepository(path))
    parser = argparse.ArgumentParser()
    add_agents_parser(parser.add_subparsers(dest="command", required=True))

    def call(*args: str) -> tuple[int, dict[str, object]]:
        status = run_agents_command(parser.parse_args(["agents", *args]))
        return status, json.loads(capsys.readouterr().out)

    status, report = call("provider-budget-status")
    assert status == 0 and report["configured"] is False
    status, report = call("configure-provider-budget", "--task-output-tokens", "100")
    assert status == 2 and report["error"] == "AGENT_INPUT_OR_RUN_BLOCKED"
    limits = ("--task-output-tokens", "100", "--family-output-tokens", "200",
              "--daily-output-tokens", "300")
    status, report = call("configure-provider-budget", *limits)
    assert status == 0 and report["configured"] is True
    assert report["reserved_lifetime"] == 0
    assert call("configure-provider-budget", *limits)[0] == 0
    status, report = call("configure-provider-budget", "--task-output-tokens", "101",
                          "--family-output-tokens", "200", "--daily-output-tokens", "300")
    assert status == 2 and report["error"] == "PROVIDER_BUDGET_POLICY_CONFLICT"
    assert call("provider-budget-status")[1]["task_limit"] == 100
