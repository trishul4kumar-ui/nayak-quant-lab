from __future__ import annotations

import argparse
import json
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from tests.agents.conftest import NOW
from tests.agents.test_bear import BearFixtureProvider
from tests.agents.test_bull import ResearchFixtureProvider, snapshot

from quantlab.agents.bear import BearWorker, create_bear_context
from quantlab.agents.bull import BullWorker, create_bull_context
from quantlab.agents.cli import add_agents_parser, run_agents_command
from quantlab.agents.context import FrozenHistory
from quantlab.agents.contracts import AgentRole, ResearchMode
from quantlab.agents.debate import DebateWorker, create_debate, verify_transcript
from quantlab.agents.debate_contracts import (
    DebateStatus,
    DebateTranscript,
    FrozenCritique,
)
from quantlab.agents.errors import AgentContextError
from quantlab.agents.hashing import digest
from quantlab.agents.provider import StructuredRequest, UnavailableProvider
from quantlab.agents.repository import AgentRepository
from quantlab.agents.tool_contracts import AgentToolResult
from quantlab.realtime_data.freeze import freeze
from quantlab.realtime_data.mock import seed_observations


class DebateFixtureProvider(ResearchFixtureProvider):
    def __init__(self, role: AgentRole, fault: str = "", request_tool: bool = False) -> None:
        super().__init__("NO_TRADE")
        self.role, self.debate_fault, self.request_tool = role, fault, request_tool
        self.after_critique = lambda: None

    def memo_payload(self, scope: list[str], results: list[dict]) -> dict:
        if self.role is AgentRole.BEAR:
            return BearFixtureProvider("NO_TRADE").memo_payload(scope, results)
        return super().memo_payload(scope, results)

    def generate_structured(self, request: StructuredRequest) -> str:
        schema = json.loads(request.schema_json)
        if schema["title"] not in {"CritiqueDraft", "RebuttalDraft"}:
            return super().generate_structured(request)
        self.calls += 1
        self.requests.append(request)
        evidence = json.loads(dict(request.sections)["UNTRUSTED EVIDENCE"])
        refs = [evidence["shared_evidence"][0]["hash"]]
        if schema["title"] == "RebuttalDraft":
            return json.dumps(
                {
                    "respondent_agent": self.role,
                    "target_critique_hash": evidence["target_critique"]["content_hash"],
                    "responses": ["The requested empirical validation remains incomplete"],
                    "concessions": ["The initial thesis does not establish independent edge"],
                    "unresolved_questions": [
                        "Out-of-sample and trading cost survival need testing"
                    ],
                    "evidence_refs": refs,
                }
            )
        other = AgentRole.BEAR if self.role is AgentRole.BULL else AgentRole.BULL
        payload = {
            "critic_agent": self.role,
            "target_memo_hash": evidence["initial_memos"][other]["content_hash"],
            "claims_challenged": ["The economic interpretation is unvalidated"],
            "evidence_conflicts": ["Descriptive evidence does not prove independent edge"],
            "missing_tests": ["oos_walk_forward", "cost_resilience"],
            "alternative_explanations": ["Common market exposure may explain the observation"],
            "factor_objections": ["Beta is descriptive, not validated residual alpha"],
            "regime_objections": [],
            "cost_liquidity_objections": ["Cost evidence unavailable"],
            "invalidation_evidence": [],
            "unsupported_claims": ["Predictive edge not established"],
            "severity": "WARN",
            "critic_confidence": 0.5,
            "evidence_refs": refs,
            "requests": [
                {
                    "tool": "query_feature",
                    "analysis_id": "momentum",
                    "security_id": None,
                    "lookback": 20,
                }
            ]
            if self.request_tool
            else [],
        }
        if self.debate_fault == "foreign_ref":
            payload["evidence_refs"] = [digest("foreign")]
        if self.debate_fault == "target":
            payload["target_memo_hash"] = digest("foreign")
        if self.debate_fault == "recursive":
            payload["requests"] *= 4
        if self.debate_fault == "sizing":
            payload["quantity"] = 10
        if self.debate_fault == "live_tool":
            payload["requests"] = [
                {
                    "tool": "place_live_order",
                    "analysis_id": None,
                    "security_id": None,
                    "lookback": 20,
                }
            ]
        if self.debate_fault == "timeout":
            time.sleep(0.2)
        self.after_critique()
        return json.dumps(payload)


class DeskFixtureProvider(DebateFixtureProvider):
    """One test transport dispatches by the actual host-owned role section."""

    def __init__(self) -> None:
        super().__init__(AgentRole.BULL)

    def generate_structured(self, request: StructuredRequest) -> str:
        context = json.loads(dict(request.sections)["FROZEN CONTEXT SUMMARY"])
        self.role = AgentRole(context["agent"])
        return super().generate_structured(request)


def initial_pair(repository: AgentRepository, *, snap=None, now=NOW):
    snap = snap or snapshot()
    providers = {role: DebateFixtureProvider(role) for role in AgentRole}
    memos = {}
    for role, factory, worker in (
        (AgentRole.BULL, create_bull_context, BullWorker),
        (AgentRole.BEAR, create_bear_context, BearWorker),
    ):
        context = factory(repository, snap, providers[role], now=now, mode=ResearchMode.REPLAY)
        run = worker(repository, providers[role], clock=lambda: now).run(context)
        assert run.memo_hash
        memos[role] = run.memo_hash
    session = create_debate(repository, memos[AgentRole.BULL], memos[AgentRole.BEAR], now=now)
    return session, providers


def test_bounded_debate_shared_evidence_and_restart(tmp_path: Path) -> None:
    path = tmp_path / "debate.sqlite"
    repository = AgentRepository(path)
    session, providers = initial_pair(repository)
    providers[AgentRole.BULL].request_tool = True
    transcript = DebateWorker(repository, providers, clock=lambda: NOW).run(session)
    assert transcript.status is DebateStatus.COMPLETE
    assert len(transcript.critiques) == 2 and not transcript.rebuttals
    assert [p.calls for p in providers.values()] == [3, 3]
    assert not transcript.execution_authority
    verify_transcript(repository, transcript)
    first = repository.get(transcript.critiques[0], FrozenCritique)
    added = first.tool_result_hashes[0]
    bear_request = json.loads(
        dict(providers[AgentRole.BEAR].requests[-1].sections)["UNTRUSTED EVIDENCE"]
    )
    assert added in {row["hash"] for row in bear_request["shared_evidence"]}
    assert all(check.status == "NOT_TESTED" for check in transcript.falsification_checks)
    assert len(transcript.falsification_checks) == 10
    assert all(not edge.interpretation_verified for edge in transcript.evidence_graph)
    for key in transcript.evidence_hashes:
        assert repository.get(key, AgentToolResult).snapshot_hash == session.snapshot_hash
    serialized = transcript.model_dump_json()
    assert DebateTranscript.model_validate_json(serialized).content_hash == transcript.content_hash
    repository.close()
    repository = AgentRepository(path)
    try:
        verify_transcript(repository, repository.get(transcript.content_hash, DebateTranscript))
        assert DebateWorker(repository, providers, clock=lambda: NOW).run(session) == transcript
        assert [p.calls for p in providers.values()] == [3, 3]
    finally:
        repository.close()


def test_optional_one_rebuttal_each_then_stop(repository: AgentRepository) -> None:
    session, providers = initial_pair(repository)
    session = create_debate(
        repository, session.bull_memo_hash, session.bear_memo_hash, now=NOW, include_rebuttals=True
    )
    transcript = DebateWorker(repository, providers, clock=lambda: NOW).run(session)
    assert transcript.status is DebateStatus.COMPLETE
    assert len(transcript.critiques) == len(transcript.rebuttals) == 2
    assert [p.calls for p in providers.values()] == [4, 4]
    verify_transcript(repository, transcript)


@pytest.mark.parametrize("fault", ["foreign_ref", "target", "sizing", "recursive", "live_tool"])
def test_invalid_critique_never_fabricates_completion(
    repository: AgentRepository, fault: str
) -> None:
    session, providers = initial_pair(repository)
    providers[AgentRole.BULL].debate_fault = fault
    providers[AgentRole.BULL].request_tool = True
    transcript = DebateWorker(repository, providers, clock=lambda: NOW).run(session)
    assert transcript.status is DebateStatus.INCOMPLETE
    assert not transcript.critiques and not transcript.rebuttals
    assert providers[AgentRole.BULL].calls <= 4  # two initials, critique + at most one retry
    assert providers[AgentRole.BEAR].calls == 2


def test_timeout_and_unavailable_agent_do_not_invent_a_view(repository: AgentRepository) -> None:
    session, providers = initial_pair(repository)
    providers[AgentRole.BULL].debate_fault = "timeout"
    transcript = DebateWorker(repository, providers, clock=lambda: NOW, timeout_seconds=0.02).run(
        session
    )
    assert (
        transcript.status is DebateStatus.INCOMPLETE and transcript.error_code == "PROVIDER_TIMEOUT"
    )
    assert not transcript.critiques
    session = create_debate(
        repository, session.bull_memo_hash, session.bear_memo_hash, now=NOW, include_rebuttals=True
    )
    transcript = DebateWorker(
        repository, {AgentRole.BULL: UnavailableProvider()}, clock=lambda: NOW
    ).run(session)
    assert transcript.status is DebateStatus.INCOMPLETE
    assert transcript.error_code == "DEBATE_AGENT_UNAVAILABLE" and not transcript.critiques


def test_snapshot_expiry_rejects_late_critique(repository: AgentRepository) -> None:
    session, providers = initial_pair(repository)
    clock = [NOW]
    providers[AgentRole.BULL].after_critique = lambda: clock.__setitem__(0, session.expires_at)
    transcript = DebateWorker(repository, providers, clock=lambda: clock[0]).run(session)
    assert transcript.status is DebateStatus.STALE and not transcript.critiques


def test_new_snapshot_new_version_and_mixed_snapshots_block(repository: AgentRepository) -> None:
    old, _ = initial_pair(repository)
    rows = seed_observations()
    new, _ = initial_pair(
        repository,
        snap=freeze(rows, as_of=max(r.processing_time for r in rows) + timedelta(seconds=1)),
    )
    assert old.snapshot_hash != new.snapshot_hash and old.debate_id != new.debate_id
    with pytest.raises(AgentContextError, match="BOUNDARY_MISMATCH"):
        create_debate(repository, old.bull_memo_hash, new.bear_memo_hash, now=NOW)


def test_interrupted_debate_claim_blocks_model_replay(repository: AgentRepository) -> None:
    session, providers = initial_pair(repository)
    assert repository.claim_run(session.debate_id, session.content_hash)
    with pytest.raises(AgentContextError, match="CLAIMED_OR_INTERRUPTED"):
        DebateWorker(repository, providers, clock=lambda: NOW).run(session)
    assert [p.calls for p in providers.values()] == [2, 2]


def test_same_history_with_different_freeze_clocks_is_one_evidence_boundary(
    repository: AgentRepository,
) -> None:
    from tests.agents.test_bull import make_context

    from quantlab.agents.contracts import AgentRunContext

    bull_provider = DebateFixtureProvider(AgentRole.BULL)
    context = make_context(repository, bull_provider, with_history=True)
    bull = BullWorker(repository, bull_provider, clock=lambda: NOW).run(context)
    history = repository.get(context.history_hash, FrozenHistory)
    values = history.model_dump(mode="json", exclude={"content_hash"})
    values["created_at"] = NOW + timedelta(seconds=1)
    second_history = FrozenHistory.model_validate(values)
    bear_provider = DebateFixtureProvider(AgentRole.BEAR)
    bear_context = create_bear_context(
        repository,
        snapshot(),
        bear_provider,
        now=NOW + timedelta(seconds=1),
        history=second_history,
        mode=ResearchMode.REPLAY,
    )
    bear = BearWorker(repository, bear_provider, clock=lambda: NOW + timedelta(seconds=1)).run(
        bear_context
    )
    assert context.history_hash != bear_context.history_hash
    session = create_debate(
        repository, bull.memo_hash, bear.memo_hash, now=NOW + timedelta(seconds=2)
    )
    assert session.snapshot_hash == context.snapshot_hash
    providers = {AgentRole.BULL: bull_provider, AgentRole.BEAR: bear_provider}
    transcript = DebateWorker(repository, providers, clock=lambda: NOW + timedelta(seconds=2)).run(
        session
    )
    assert transcript.status is DebateStatus.COMPLETE
    assert (
        repository.get(session.bull_context_hash, AgentRunContext).history_hash
        == history.content_hash
    )


def test_cancel_rejects_late_critique(repository: AgentRepository) -> None:
    session, providers = initial_pair(repository)
    cancel = threading.Event()
    providers[AgentRole.BULL].after_critique = cancel.set
    transcript = DebateWorker(repository, providers, clock=lambda: NOW).run(session, cancel=cancel)
    assert transcript.status is DebateStatus.INCOMPLETE
    assert transcript.error_code == "PROVIDER_CANCELLED" and not transcript.critiques


@pytest.mark.parametrize("fault", ["target", "falsification"])
def test_resealed_forged_transcript_cannot_promote_arguments_or_wrong_targets(
    repository: AgentRepository,
    fault: str,
) -> None:
    session, providers = initial_pair(repository)
    transcript = DebateWorker(repository, providers, clock=lambda: NOW).run(session)
    values = transcript.model_dump(mode="json", exclude={"content_hash"})
    if fault == "target":
        critique = repository.get(transcript.critiques[0], FrozenCritique)
        bad = critique.model_dump(mode="json", exclude={"content_hash"})
        bad["draft"]["target_memo_hash"] = session.bull_memo_hash
        replacement = repository.put(FrozenCritique.model_validate(bad))
        values["critiques"][0] = replacement.content_hash
    else:
        check = transcript.falsification_checks[0]
        from quantlab.agents.debate_contracts import FalsificationCheck

        bad = check.model_dump(mode="json", exclude={"content_hash"})
        bad["status"] = "PASS"
        values["falsification_checks"][0] = FalsificationCheck.model_validate(bad).model_dump(
            mode="json"
        )
    forged = DebateTranscript.model_validate(values)
    with pytest.raises(AgentContextError, match="MISMATCH"):
        verify_transcript(repository, forged)


def test_cli_debate_and_verified_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "cli.sqlite"
    repo = AgentRepository(path)
    session, _ = initial_pair(repo, now=datetime.now(UTC))
    repo.close()
    provider = DeskFixtureProvider()
    monkeypatch.setattr("quantlab.agents.cli.configured_provider", lambda: provider)
    monkeypatch.setattr("quantlab.agents.cli.AgentRepository", lambda: AgentRepository(path))
    parser = argparse.ArgumentParser()
    add_agents_parser(parser.add_subparsers())
    args = parser.parse_args(
        [
            "agents",
            "run-debate",
            "--bull-memo",
            session.bull_memo_hash,
            "--bear-memo",
            session.bear_memo_hash,
        ]
    )
    assert run_agents_command(args) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "COMPLETE"
    args = parser.parse_args(["agents", "debate-history", "--query", session.snapshot_hash])
    assert run_agents_command(args) == 0
    assert len(json.loads(capsys.readouterr().out)) == 1 and provider.calls == 2
