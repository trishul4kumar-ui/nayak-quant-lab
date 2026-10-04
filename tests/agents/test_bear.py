from __future__ import annotations

import argparse
import json
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError
from tests.agents.conftest import NOW
from tests.agents.test_bull import ResearchFixtureProvider, make_context, snapshot

from quantlab.agents.bear import BearWorker, bear_mandate, create_bear_context, search_bear_history
from quantlab.agents.bull import BullWorker, bull_mandate, search_bull_history
from quantlab.agents.cli import add_agents_parser, run_agents_command
from quantlab.agents.context import FrozenHistory
from quantlab.agents.contracts import (
    AgentRunContext,
    AgentState,
    EvidenceStatus,
    ResearchMode,
    Stance,
)
from quantlab.agents.errors import AgentContextError
from quantlab.agents.repository import AgentRepository
from quantlab.agents.research import (
    BearMemoDraft,
    BearResearchMemo,
    BullResearchMemo,
    ResearchScreen,
)
from quantlab.agents.tool_contracts import AgentToolResult
from quantlab.realtime_data.models import QualityStatus


class BearFixtureProvider(ResearchFixtureProvider):
    """Test only: independent downside output, never reads Bull's memo."""

    def __init__(self, stance: str = "AVOID", fault: str = "") -> None:
        super().__init__(stance, fault)

    def memo_payload(self, scope: list[str], results: list[dict]) -> dict:
        payload = super().memo_payload(scope, results)
        payload.update(
            hypothesis="Downside fragility may warrant avoiding exposure "
            "until participation recovers",
            economic_rationale="Crowded factor exposure and deteriorating participation "
            "can amplify losses",
            exposure="INTRADAY_SHORT_RESEARCH" if self.stance == "SHORT_CANDIDATE" else "AVOID",
            squeeze_reversal_risks=["A broad participation recovery could squeeze a short thesis"],
            liquidity_risks=["Executable spread and depth support are not established"],
            entry="MORE_RESEARCH",
        )
        if self.fault == "eligibility":
            payload["instrument_eligibility"] = "PASS"
        if self.fault == "no_invalidation":
            payload["invalidation_conditions"] = []
        if self.fault == "no_squeeze":
            payload["squeeze_reversal_risks"] = []
        if self.stance == "NO_TRADE":
            payload["no_trade_reason"] = "Downside thesis invalidated by a participation recovery"
        return payload


def bear_context(repository: AgentRepository, provider: BearFixtureProvider) -> AgentRunContext:
    # Both analysts receive identical immutable source data, not each other's interpretation.
    bull_context = make_context(repository, provider, with_history=True)
    history = repository.get(bull_context.history_hash, FrozenHistory)
    return create_bear_context(
        repository, snapshot(), provider, now=NOW, history=history, mode=ResearchMode.REPLAY
    )


def test_bear_independent_downside_memo_and_permission_symmetry(
    repository: AgentRepository,
) -> None:
    bull = ResearchFixtureProvider("NO_TRADE")
    bull_context = make_context(repository, bull, with_history=True)
    bull_run = BullWorker(repository, bull, clock=lambda: NOW).run(bull_context)
    bull_memo = repository.get(bull_run.memo_hash, BullResearchMemo)
    provider = BearFixtureProvider()
    context = bear_context(repository, provider)
    run = BearWorker(repository, provider, clock=lambda: NOW).run(context)
    assert run.state is AgentState.FROZEN and run.memo_hash
    memo = repository.get(run.memo_hash, BearResearchMemo)
    assert memo.stance is Stance.AVOID
    assert memo.thesis.hypothesis != bull_memo.thesis.hypothesis
    assert context.snapshot_hash == bull_context.snapshot_hash
    assert context.history_hash == bull_context.history_hash
    assert context.security_scope == bull_context.security_scope
    assert context.as_of == bull_context.as_of
    assert bull_mandate(NOW).granted == bear_mandate(NOW).granted
    assert bull_mandate(NOW).content_hash != bear_mandate(NOW).content_hash
    for request in provider.requests:
        evidence = json.loads(dict(request.sections)["UNTRUSTED EVIDENCE"])
        assert not evidence["known_prior_own_theses"]
        assert bull_memo.thesis.hypothesis not in json.dumps(request.sections)
        assert bull_memo.content_hash not in json.dumps(request.sections)
    assert provider.calls == 2 and len(run.tool_result_hashes) == 9
    assert memo.instrument_eligibility == "UNKNOWN"
    assert "eligibility UNKNOWN" in memo.preferred_exposure
    assert memo.squeeze_reversal_risks and memo.liquidity_risks
    assert memo.calibrated_confidence is None and memo.outcome_status == "NOT_TESTED"
    assert memo.validation is EvidenceStatus.NOT_TESTED
    for ref in (*memo.evidence_for, *memo.evidence_against):
        assert (
            repository.get(ref.artifact_hash, AgentToolResult).context_hash == context.content_hash
        )
    bull_screen = repository.get(bull_memo.screen_hash, ResearchScreen)
    bear_screen = repository.get(memo.screen_hash, ResearchScreen)
    assert bear_screen.research_queue == tuple(reversed(bull_screen.research_queue))
    assert search_bear_history(repository, "fragility") == (memo,)
    assert search_bull_history(repository) == (bull_memo,)


def test_short_is_not_trade_ready_without_validation_or_eligibility(
    repository: AgentRepository,
) -> None:
    provider = BearFixtureProvider("SHORT_CANDIDATE")
    context = bear_context(repository, provider)
    run = BearWorker(repository, provider, clock=lambda: NOW).run(context)
    memo = repository.get(run.memo_hash, BearResearchMemo)
    assert memo.stance is Stance.MORE_RESEARCH
    assert memo.instrument_eligibility == "UNKNOWN"
    assert memo.exposure_archetype == "INTRADAY_SHORT_RESEARCH"
    assert any("overnight cash-equity short" in row.description for row in memo.uncertainties)


@pytest.mark.parametrize(
    "fault",
    [
        "foreign_ref",
        "sizing",
        "order_price",
        "instruction_price",
        "live_tool",
        "eligibility",
        "no_invalidation",
        "no_squeeze",
    ],
)
def test_bear_cannot_override_host_research_boundary(
    repository: AgentRepository, fault: str
) -> None:
    provider = BearFixtureProvider(fault=fault)
    run = BearWorker(repository, provider, clock=lambda: NOW).run(
        bear_context(repository, provider)
    )
    assert run.state is AgentState.ERROR and run.memo_hash is None
    assert not repository.list(BearResearchMemo)


def test_bear_stale_and_role_mismatch_are_blocked(repository: AgentRepository) -> None:
    provider = BearFixtureProvider()
    context = bear_context(repository, provider)
    clock = [NOW]
    provider.after_memo = lambda: clock.__setitem__(0, context.expires_at)
    run = BearWorker(repository, provider, clock=lambda: clock[0]).run(context)
    assert run.state is AgentState.STALE and run.memo_hash is None
    with pytest.raises(AgentContextError, match="ROLE_REQUIRED"):
        BearWorker(repository, provider, clock=lambda: NOW).run(make_context(repository, provider))


def test_bear_missing_history_no_trade_and_restart(tmp_path: Path) -> None:
    path = tmp_path / "bear.sqlite"
    repository = AgentRepository(path)
    provider = BearFixtureProvider("NO_TRADE")
    context = create_bear_context(
        repository, snapshot(), provider, now=NOW, mode=ResearchMode.REPLAY
    )
    run = BearWorker(repository, provider, clock=lambda: NOW).run(context)
    assert run.state is AgentState.NO_TRADE and run.memo_hash
    memo = repository.get(run.memo_hash, BearResearchMemo)
    assert memo.validation is EvidenceStatus.NOT_TESTED
    assert "invalidated" in memo.no_trade_reason
    repository.close()
    repository = AgentRepository(path)
    try:
        assert repository.get(run.memo_hash, BearResearchMemo) == memo
        assert BearWorker(repository, provider, clock=lambda: NOW).run(context) == run
        assert provider.calls == 2
        assert search_bear_history(repository, "fragility") == (memo,)
        assert search_bear_history(repository, as_of=NOW - timedelta(seconds=1)) == ()
    finally:
        repository.close()


def test_bear_requires_all_seven_challenges() -> None:
    payload = BearFixtureProvider().memo_payload(["NSE:TEST"], [{"hash": "a"}] * 9)
    payload["answers"].pop()
    with pytest.raises(ValidationError):
        BearMemoDraft.model_validate(payload)


@pytest.mark.parametrize("missing", [True, False])
def test_bear_unhealthy_or_missing_market_data_blocks_before_model(
    repository: AgentRepository, missing: bool
) -> None:
    provider = BearFixtureProvider()
    snap = snapshot().model_copy(
        update={
            "observations": () if missing else snapshot().observations,
            "quality": QualityStatus.UNKNOWN,
        }
    )
    with pytest.raises(AgentContextError, match="UNHEALTHY_SNAPSHOT"):
        create_bear_context(repository, snap, provider, now=NOW, mode=ResearchMode.REPLAY)
    assert provider.calls == 0


def test_cli_bear_run_and_search(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    saved = tmp_path / "snapshot.json"
    saved.write_text(snapshot().model_dump_json())
    provider = BearFixtureProvider("NO_TRADE")
    monkeypatch.setattr("quantlab.agents.cli.configured_provider", lambda: provider)
    monkeypatch.setattr(
        "quantlab.agents.cli.AgentRepository", lambda: AgentRepository(tmp_path / "cli.sqlite")
    )
    parser = argparse.ArgumentParser()
    add_agents_parser(parser.add_subparsers())
    args = parser.parse_args(["agents", "run-bear", "--snapshot", str(saved), "--replay"])
    assert run_agents_command(args) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "NO_TRADE"
    args = parser.parse_args(["agents", "bear-history", "--query", "fragility"])
    assert run_agents_command(args) == 0
    assert json.loads(capsys.readouterr().out)[0]["instrument_eligibility"] == "UNKNOWN"
