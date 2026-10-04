"""Capture only verified canonical tool lineage; replay decisions after restart."""

from datetime import datetime

from quantlab.agents.adjudication import (
    METRIC_SPECS,
    adjudicate,
    default_adjudication_policy,
    freeze_gate_evidence,
)
from quantlab.agents.adjudication_contracts import (
    AdjudicationDecision,
    CanonicalMeasurement,
    FrozenAdjudicationInput,
    RoleAdjudicationEvidence,
)
from quantlab.agents.context import FrozenSnapshot
from quantlab.agents.contracts import AgentRunContext, EvidenceStatus
from quantlab.agents.debate import verify_transcript
from quantlab.agents.debate_contracts import DebateSession, DebateTranscript
from quantlab.agents.repository import AgentRepository
from quantlab.agents.tool_contracts import AgentToolResult


def _capture_role(
    repository: AgentRepository,
    context: AgentRunContext,
    transcript: DebateTranscript,
    now: datetime,
) -> RoleAdjudicationEvidence:
    results = tuple(repository.get(key, AgentToolResult) for key in transcript.evidence_hashes)
    results = tuple(
        row
        for row in results
        if repository.get(row.context_hash, AgentRunContext).agent.role is context.agent.role
    )
    measurements = []
    for name, tool, unit in METRIC_SPECS:
        relevant = tuple(row for row in results if row.tool is tool)
        matches = tuple(
            metric
            for row in relevant
            if row.status == "COMPLETED"
            for metric in row.metrics
            if metric.name == name and metric.security_id is None
        )
        identities = {(row.value, row.unit, row.status) for row in matches}
        status, value = EvidenceStatus.NOT_TESTED, None
        if len(identities) == 1:
            candidate, actual_unit, status = next(iter(identities))
            if actual_unit != unit:
                status = (
                    EvidenceStatus.FAIL if status is EvidenceStatus.FAIL else EvidenceStatus.UNKNOWN
                )
            else:
                value = candidate
        elif matches:
            status = (
                EvidenceStatus.FAIL
                if any(row.status is EvidenceStatus.FAIL for row in matches)
                else EvidenceStatus.UNKNOWN
            )
        measurements.append(
            CanonicalMeasurement(
                created_at=now,
                name=name,
                canonical_tool=tool,
                unit=unit,
                status=status,
                value=value,
                result_hashes=tuple(
                    sorted(
                        row.content_hash
                        for row in relevant
                        if not matches
                        or any(
                            metric.name == name and metric.security_id is None
                            for metric in row.metrics
                        )
                    )
                ),
            )
        )
    return RoleAdjudicationEvidence(
        created_at=now,
        role=context.agent.role,
        context_hash=context.content_hash,
        measurements=tuple(measurements),
        research_gate=freeze_gate_evidence(tuple(measurements), context.data_kind, now),
    )


def capture_adjudication_input(
    repository: AgentRepository,
    transcript: DebateTranscript,
    *,
    now: datetime,
) -> FrozenAdjudicationInput:
    verify_transcript(repository, transcript)
    if now.tzinfo is None or now < transcript.completed_at:
        raise ValueError("adjudication must follow transcript completion")
    session = repository.get(transcript.session_hash, DebateSession)
    bull = repository.get(session.bull_context_hash, AgentRunContext)
    bear = repository.get(session.bear_context_hash, AgentRunContext)
    snapshot = repository.get(bull.snapshot_artifact_hash, FrozenSnapshot).snapshot()
    policy = default_adjudication_policy()
    return FrozenAdjudicationInput(
        created_at=now,
        transcript_hash=transcript.content_hash,
        bull_memo_hash=session.bull_memo_hash,
        bear_memo_hash=session.bear_memo_hash,
        boundary_hash=session.boundary_hash,
        snapshot_hash=session.snapshot_hash,
        policy_hash=policy.content_hash,
        as_of=session.as_of,
        expires_at=session.expires_at,
        data_kind=bull.data_kind,
        mode=bull.mode,
        debate_status=transcript.status,
        data_quality=snapshot.quality.value,
        data_freshness=snapshot.freshness.value,
        bull=_capture_role(repository, bull, transcript, now),
        bear=_capture_role(repository, bear, transcript, now),
        evidence_refs=tuple(
            sorted(
                set(
                    transcript.evidence_hashes
                    + (
                        transcript.content_hash,
                        session.bull_memo_hash,
                        session.bear_memo_hash,
                        bull.snapshot_artifact_hash,
                    )
                )
            )
        ),
    )


def run_adjudication(
    repository: AgentRepository,
    transcript_hash: str,
    *,
    now: datetime,
) -> AdjudicationDecision:
    transcript = repository.get(transcript_hash, DebateTranscript)
    repository.put(default_adjudication_policy())
    frame = repository.put(capture_adjudication_input(repository, transcript, now=now))
    decision = repository.put(adjudicate(frame, default_adjudication_policy()))
    repository.audit(
        "ADJUDICATION_FROZEN",
        run_id=transcript.debate_id,
        now=now,
        artifact_hash=decision.content_hash,
        safe_code=decision.outcome.value,
    )
    return decision


def verify_adjudication(repository: AgentRepository, decision: AdjudicationDecision) -> None:
    decision.verified()
    policy = default_adjudication_policy()
    if decision.policy_hash != policy.content_hash:
        raise ValueError("unregistered adjudication policy")
    repository.get(policy.content_hash, type(policy))
    frame = repository.get(decision.input_hash, FrozenAdjudicationInput)
    transcript = repository.get(frame.transcript_hash, DebateTranscript)
    captured = capture_adjudication_input(repository, transcript, now=frame.created_at)
    if captured != frame or adjudicate(frame, policy) != decision:
        raise ValueError("adjudication evidence or decision mismatch")
