from __future__ import annotations

import argparse
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError
from tests.agents.conftest import NOW
from tests.agents.test_debate import initial_pair

from quantlab.agents.adjudication import (
    METRIC_SPECS,
    adjudicate,
    default_adjudication_policy,
    freeze_gate_evidence,
)
from quantlab.agents.adjudication_contracts import (
    AdjudicationDecision,
    AdjudicationOutcome,
    CanonicalMeasurement,
    FrozenAdjudicationInput,
    RoleAdjudicationEvidence,
)
from quantlab.agents.adjudication_service import (
    capture_adjudication_input,
    run_adjudication,
    verify_adjudication,
)
from quantlab.agents.cli import add_agents_parser, run_agents_command
from quantlab.agents.contracts import AgentRole, DataKind, EvidenceStatus, ResearchMode
from quantlab.agents.debate import DebateWorker
from quantlab.agents.debate_contracts import DebateStatus, FrozenCritique
from quantlab.agents.hashing import Artifact, digest
from quantlab.agents.repository import AgentRepository


def reseal(artifact: Artifact, **updates):
    return type(artifact).model_validate(
        {
            **artifact.model_dump(mode="python", exclude={"content_hash"}),
            **updates,
        }
    )


def role_evidence(role: AgentRole, *, strong: bool) -> RoleAdjudicationEvidence:
    values = {
        "integrity": 1,
        "test_set_integrity": 1,
        "next_bar_fill": 1,
        "walk_forward_windows": 5,
        "oos_sharpe": 1.8 if strong else 0.2,
        "cost_survival_20bps": 1,
        "parameter_fragility": 0,
        "statistical_evidence": None,
        "multiple_testing": None,
        "n_hypotheses": 1,
        "robustness": 0.9 if strong else 0.3,
        "factor_independence": 0.8 if strong else 0.2,
        "regime_fit": 0.8 if strong else 0.1,
        "model_evaluation": None,
        "ensemble_evaluation": None,
        "expected_edge_bps": 18 if strong else 6,
        "estimated_cost_bps": 3,
        "liquidity": 1,
        "canonical_contradiction": 0,
        "risk_clear": 1,
    }
    measurements = tuple(
        CanonicalMeasurement(
            created_at=NOW,
            name=name,
            canonical_tool=tool,
            unit=unit,
            status=EvidenceStatus.PASS,
            value=values[name],
            result_hashes=(digest((role, tool)),),
        )
        for name, tool, unit in METRIC_SPECS
    )
    return RoleAdjudicationEvidence(
        created_at=NOW,
        role=role,
        context_hash=digest(role),
        measurements=measurements,
        research_gate=freeze_gate_evidence(measurements, DataKind.REAL, NOW),
    )


def frame(*, strong_bear: bool = False) -> FrozenAdjudicationInput:
    return FrozenAdjudicationInput(
        created_at=NOW,
        transcript_hash=digest("transcript"),
        bull_memo_hash=digest("bull"),
        bear_memo_hash=digest("bear"),
        boundary_hash=digest("boundary"),
        snapshot_hash=digest("snapshot"),
        policy_hash=default_adjudication_policy().content_hash,
        as_of=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(seconds=60),
        data_kind=DataKind.REAL,
        mode=ResearchMode.RESEARCH,
        debate_status=DebateStatus.COMPLETE,
        data_quality="valid",
        data_freshness="fresh",
        bull=role_evidence(AgentRole.BULL, strong=True),
        bear=role_evidence(AgentRole.BEAR, strong=strong_bear),
        evidence_refs=(digest("canonical"),),
    )


def change_metric(
    frame_input: FrozenAdjudicationInput, name: str, **updates
) -> FrozenAdjudicationInput:
    rows = tuple(
        reseal(row, **updates) if row.name == name else row for row in frame_input.bull.measurements
    )
    return reseal(
        frame_input,
        bull=reseal(
            frame_input.bull,
            measurements=rows,
            research_gate=freeze_gate_evidence(rows, frame_input.data_kind, frame_input.created_at),
        ),
    )


def test_pure_determinism_and_non_execution_contract() -> None:
    value, policy = frame(), default_adjudication_policy()
    first = adjudicate(value, policy)
    second = adjudicate(
        FrozenAdjudicationInput.model_validate_json(value.model_dump_json()), policy
    )
    assert first == second and first.model_dump_json() == second.model_dump_json()
    assert first.outcome is AdjudicationOutcome.BULL_DOMINANT
    assert first.bull_score > first.bear_score and not first.hard_blockers
    assert not first.execution_authority
    assert "RAW_CONFIDENCE_AND_PROSE_NOT_SCORED" in first.warnings
    assert all(
        component.weight == 0
        for component in first.score_components
        if component.name == "agent_calibration"
    )
    with pytest.raises(ValidationError):
        reseal(first, execution_authority=True)
    with pytest.raises(ValidationError):
        reseal(first, quantity=10)


@pytest.mark.parametrize(
    "name,updates,outcome",
    [
        ("integrity", {"status": EvidenceStatus.FAIL}, AdjudicationOutcome.VALIDATION_BLOCKED),
        ("test_set_integrity", {"value": 0}, AdjudicationOutcome.VALIDATION_BLOCKED),
        (
            "model_evaluation",
            {"status": EvidenceStatus.NOT_TESTED},
            AdjudicationOutcome.INSUFFICIENT_DATA,
        ),
        ("expected_edge_bps", {"value": 3}, AdjudicationOutcome.NO_EDGE),
        ("expected_edge_bps", {"value": -1}, AdjudicationOutcome.NO_EDGE),
        ("expected_edge_bps", {"value": 5}, AdjudicationOutcome.NO_EDGE),
        ("liquidity", {"value": 0.1}, AdjudicationOutcome.LIQUIDITY_BLOCKED),
        ("liquidity", {"status": EvidenceStatus.UNKNOWN}, AdjudicationOutcome.LIQUIDITY_BLOCKED),
        ("risk_clear", {"value": 0}, AdjudicationOutcome.RISK_BLOCKED),
        ("risk_clear", {"status": EvidenceStatus.FAIL}, AdjudicationOutcome.RISK_BLOCKED),
        ("canonical_contradiction", {"value": 0.5}, AdjudicationOutcome.CONFLICTED),
        (
            "statistical_evidence",
            {"status": EvidenceStatus.WARN},
            AdjudicationOutcome.INSUFFICIENT_DATA,
        ),
    ],
)
def test_hard_blockers_override_scores(name, updates, outcome) -> None:
    result = adjudicate(change_metric(frame(), name, **updates), default_adjudication_policy())
    assert result.outcome is outcome
    assert result.no_trade and result.hard_blockers and not result.execution_authority


@pytest.mark.parametrize(
    "updates",
    [
        {"expires_at": NOW},
        {"data_quality": "stale"},
        {"data_freshness": "unknown"},
        {"as_of": NOW - timedelta(seconds=301)},
        {"debate_status": DebateStatus.INCOMPLETE},
    ],
)
def test_bad_boundary_or_incomplete_debate_abstains(updates) -> None:
    result = adjudicate(reseal(frame(), **updates), default_adjudication_policy())
    assert result.no_trade and result.outcome is AdjudicationOutcome.INSUFFICIENT_DATA


def test_conflicted_low_confidence_bear_and_replay_outcomes() -> None:
    policy = default_adjudication_policy()
    assert adjudicate(frame(strong_bear=True), policy).outcome is AdjudicationOutcome.CONFLICTED
    weak = reseal(frame(), bull=role_evidence(AgentRole.BULL, strong=False))
    assert adjudicate(weak, policy).outcome is AdjudicationOutcome.LOW_CONFIDENCE
    bear = reseal(weak, bear=role_evidence(AgentRole.BEAR, strong=True))
    assert adjudicate(bear, policy).outcome is AdjudicationOutcome.BEAR_DOMINANT
    for updates in ({"mode": ResearchMode.REPLAY}, {"data_kind": DataKind.SYNTHETIC}):
        original = frame()
        if "data_kind" in updates:
            original = reseal(
                original,
                bull=reseal(
                    original.bull,
                    research_gate=freeze_gate_evidence(
                        original.bull.measurements, DataKind.SYNTHETIC, NOW
                    ),
                ),
                bear=reseal(
                    original.bear,
                    research_gate=freeze_gate_evidence(
                        original.bear.measurements, DataKind.SYNTHETIC, NOW
                    ),
                ),
            )
        result = adjudicate(reseal(original, **updates), policy)
        assert (
            result.no_trade
            and "SYNTHETIC_OR_REPLAY_NOT_CURRENT_MARKET_EVIDENCE" in result.hard_blockers
        )


@pytest.mark.parametrize(
    "name,updates",
    [
        ("liquidity", {"value": 1.1}),
        ("risk_clear", {"value": 0.2}),
        ("n_hypotheses", {"value": 1.5}),
        ("n_hypotheses", {"value": 0}),
        ("estimated_cost_bps", {"unit": "percent"}),
    ],
)
def test_invalid_numeric_domains_and_units_rejected(name, updates) -> None:
    with pytest.raises(ValueError):
        adjudicate(change_metric(frame(), name, **updates), default_adjudication_policy())


def test_policy_immutable_and_new_host_version_has_distinct_identity() -> None:
    policy = default_adjudication_policy()
    with pytest.raises(ValidationError):
        policy.minimum_score = 0
    with pytest.raises(ValidationError):
        policy.components[0].weight = 0
    updated = reseal(policy, policy_id="43-v2-test")
    assert updated.content_hash != policy.content_hash
    first = adjudicate(frame(), policy)
    second = adjudicate(reseal(frame(), policy_hash=updated.content_hash), updated)
    assert first.outcome is second.outcome and first.content_hash != second.content_hash
    with pytest.raises(ValueError):
        adjudicate(frame(), updated)
    with pytest.raises(ValidationError):
        reseal(policy, components=policy.components[:-2])


def test_actual_unbound_evidence_is_blocked_durable_and_resists_resealed_forgery(
    tmp_path: Path,
) -> None:
    path = tmp_path / "desk.sqlite"
    repository = AgentRepository(path)
    session, providers = initial_pair(repository)
    transcript = DebateWorker(repository, providers, clock=lambda: NOW).run(session)
    counts = [provider.calls for provider in providers.values()]
    decision = run_adjudication(repository, transcript.content_hash, now=NOW)
    assert decision.no_trade and decision.outcome is AdjudicationOutcome.INSUFFICIENT_DATA
    assert len(decision.hard_blockers) >= 40
    assert all(row.normalized_value is None for row in decision.score_components)
    assert [provider.calls for provider in providers.values()] == counts
    verify_adjudication(repository, decision)
    repository.close()
    repository = AgentRepository(path)
    restored = repository.get(decision.content_hash, AdjudicationDecision)
    verify_adjudication(repository, restored)
    assert restored == decision
    forged = reseal(decision, bull_score=100)
    with pytest.raises(ValueError):
        verify_adjudication(repository, forged)
    frozen = repository.get(decision.input_hash, FrozenAdjudicationInput)
    foreign = repository.put(reseal(frozen, boundary_hash=digest("different")))
    forged = reseal(decision, input_hash=foreign.content_hash)
    with pytest.raises(ValueError):
        verify_adjudication(repository, forged)
    changed_policy = repository.put(reseal(default_adjudication_policy(), policy_id="agent-edited"))
    with pytest.raises(ValueError):
        verify_adjudication(repository, reseal(decision, policy_hash=changed_policy.content_hash))
    repository.close()


def test_prose_confidence_and_severity_restyling_cannot_change_quantitative_result(
    tmp_path: Path,
) -> None:
    repository = AgentRepository(tmp_path / "desk.sqlite")
    session, providers = initial_pair(repository)
    transcript = DebateWorker(repository, providers, clock=lambda: NOW).run(session)
    first = run_adjudication(repository, transcript.content_hash, now=NOW)
    critique = repository.get(transcript.critiques[0], FrozenCritique)
    draft = type(critique.draft).model_validate(
        {
            **critique.draft.model_dump(),
            "claims_challenged": ["Forceful narrative phrasing has no mathematical authority"],
            "critic_confidence": 0.99,
            "severity": "CRITICAL",
        }
    )
    restyled = repository.put(reseal(critique, draft=draft))
    changed = repository.put(
        reseal(transcript, critiques=(restyled.content_hash, transcript.critiques[1]))
    )
    second = run_adjudication(repository, changed.content_hash, now=NOW)
    assert first.result_hash == second.result_hash
    assert first.outcome is second.outcome and first.bull_score == second.bull_score
    assert first.hard_blockers == second.hard_blockers
    assert first.content_hash != second.content_hash  # honest immutable lineage changed
    repository.close()


def test_cli_missing_transcript_and_verified_history(tmp_path: Path, monkeypatch, capsys) -> None:
    path = tmp_path / "desk.sqlite"
    repository = AgentRepository(path)
    session, providers = initial_pair(repository)
    transcript = DebateWorker(repository, providers, clock=lambda: NOW).run(session)
    repository.close()
    monkeypatch.setattr("quantlab.agents.cli.AgentRepository", lambda: AgentRepository(path))
    parser = argparse.ArgumentParser()
    add_agents_parser(parser.add_subparsers(dest="command"))
    assert run_agents_command(parser.parse_args(["agents", "adjudicate"])) == 2
    assert "BLOCKED" in capsys.readouterr().out
    assert (
        run_agents_command(
            parser.parse_args(["agents", "adjudicate", "--transcript", transcript.content_hash])
        )
        == 2
    )
    assert '"no_trade": true' in capsys.readouterr().out
    assert run_agents_command(parser.parse_args(["agents", "adjudication-history"])) == 0
    assert "policy_id" in capsys.readouterr().out


def test_capture_rejects_decision_before_transcript(tmp_path: Path) -> None:
    repository = AgentRepository(tmp_path / "desk.sqlite")
    session, providers = initial_pair(repository)
    transcript = DebateWorker(repository, providers, clock=lambda: NOW).run(session)
    with pytest.raises(ValueError):
        capture_adjudication_input(repository, transcript, now=NOW - timedelta(seconds=1))
    repository.close()
