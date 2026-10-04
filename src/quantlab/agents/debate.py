"""Finite, durable critique protocol; no judge model, recursion or execution path."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime

from quantlab.agents.bear import bear_mandate
from quantlab.agents.bull import bull_mandate
from quantlab.agents.context import FrozenHistory, FrozenSnapshot, validate_context
from quantlab.agents.contracts import (
    AgentRole,
    AgentRunContext,
    AgentRunRecord,
    AgentState,
    AgentVersion,
)
from quantlab.agents.debate_contracts import (
    CritiqueDraft,
    DebateProtocol,
    DebateSession,
    DebateStatus,
    DebateTranscript,
    EvidenceGraphEdge,
    EvidenceRelation,
    FrozenCritique,
    FrozenRebuttal,
    RebuttalDraft,
)
from quantlab.agents.errors import AgentContextError, AgentError, AgentProviderError
from quantlab.agents.falsification import CHECK_ROUTES, checks_from_results
from quantlab.agents.hashing import digest
from quantlab.agents.prompts import SYSTEM_SAFETY_POLICY, prompt_sections
from quantlab.agents.provider import AgentModelProvider, ProviderRunner, StructuredRequest
from quantlab.agents.repository import AgentRepository
from quantlab.agents.research import AnalystResearchMemo, BearResearchMemo, BullResearchMemo
from quantlab.agents.tool_contracts import AgentToolRequest, AgentToolResult, ToolArguments
from quantlab.agents.tool_gateway import AgentToolGateway


def protocol() -> DebateProtocol:
    return DebateProtocol(created_at=datetime(2026, 10, 4, tzinfo=UTC))


def _boundary(repository: AgentRepository, context: AgentRunContext) -> str:
    history = repository.get(context.history_hash, FrozenHistory) if context.history_hash else None
    return digest(
        {
            "snapshot": repository.get(
                context.snapshot_artifact_hash, FrozenSnapshot
            ).canonical_snapshot_json,
            "history": history.model_dump(mode="json", exclude={"created_at", "content_hash"})
            if history
            else None,
            "as_of": context.as_of.isoformat(),
            "mode": context.mode,
            "scope": context.security_scope,
            "universe": context.universe_hash,
            "data_kind": context.data_kind,
            "sources": [
                (row.name, row.version, row.source_hash) for row in context.source_versions
            ],
        }
    )


def create_debate(
    repository: AgentRepository,
    bull_memo_hash: str,
    bear_memo_hash: str,
    *,
    now: datetime,
    include_rebuttals: bool = False,
) -> DebateSession:
    bull = repository.get(bull_memo_hash, BullResearchMemo)
    bear = repository.get(bear_memo_hash, BearResearchMemo)
    contexts = [repository.get(m.context_hash, AgentRunContext) for m in (bull, bear)]
    for memo, context, role in zip((bull, bear), contexts, AgentRole, strict=True):
        validate_context(repository, context, now)
        if (
            memo.agent.role is not role
            or memo.agent != context.agent
            or (
                memo.snapshot_hash != context.snapshot_hash
                or memo.as_of != context.as_of
                or memo.model_hash != context.model.content_hash
                or not set(memo.security_scope) <= set(context.security_scope)
            )
        ):
            raise AgentContextError("INITIAL_MEMO_BINDING_MISMATCH")
        run = next(
            (
                run
                for run in repository.list(AgentRunRecord)
                if run.context_hash == context.content_hash
                and run.memo_hash == memo.content_hash
                and run.state in {AgentState.FROZEN, AgentState.NO_TRADE}
            ),
            None,
        )
        if run is None:
            raise AgentContextError("INITIAL_RESEARCH_RUN_REQUIRED")
        for ref in (*memo.evidence_for, *memo.evidence_against):
            result = repository.get(ref.artifact_hash, AgentToolResult)
            if (
                ref.artifact_hash not in run.tool_result_hashes
                or result.context_hash != context.content_hash
            ):
                raise AgentContextError("INITIAL_EVIDENCE_LINEAGE_MISMATCH")
    boundary = _boundary(repository, contexts[0])
    if boundary != _boundary(repository, contexts[1]):
        raise AgentContextError("DEBATE_EVIDENCE_BOUNDARY_MISMATCH")
    policy = repository.put(protocol())
    debate_id = (
        "debate-"
        + digest(
            {
                "bull": bull.content_hash,
                "bear": bear.content_hash,
                "boundary": boundary,
                "protocol": policy.content_hash,
                "rebuttals": include_rebuttals,
            }
        )[:24]
    )
    existing = next((s for s in repository.list(DebateSession) if s.debate_id == debate_id), None)
    if existing:
        return existing
    return repository.put(
        DebateSession(
            created_at=now,
            debate_id=debate_id,
            protocol_hash=policy.content_hash,
            boundary_hash=boundary,
            snapshot_hash=bull.snapshot_hash,
            as_of=bull.as_of,
            expires_at=min(c.expires_at for c in contexts),
            bull_memo_hash=bull.content_hash,
            bear_memo_hash=bear.content_hash,
            bull_context_hash=contexts[0].content_hash,
            bear_context_hash=contexts[1].content_hash,
            include_rebuttals=include_rebuttals,
        )
    )


class DebateWorker:
    def __init__(
        self,
        repository: AgentRepository,
        providers: dict[AgentRole, AgentModelProvider],
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        timeout_seconds: float = 30,
    ) -> None:
        if not 0 < timeout_seconds <= 30:
            raise ValueError("invalid debate time budget")
        self.repository, self.providers, self.clock = repository, providers, clock
        self.timeout_seconds = timeout_seconds

    def run(
        self, session: DebateSession, *, cancel: threading.Event | None = None
    ) -> DebateTranscript:
        session = self.repository.get(session.verified().content_hash, DebateSession)
        policy = self.repository.get(session.protocol_hash, DebateProtocol)
        if policy != protocol():
            raise AgentContextError("DEBATE_PROTOCOL_MISMATCH")
        self._check(session, cancel)
        existing = next(
            (
                t
                for t in self.repository.list(DebateTranscript)
                if t.session_hash == session.content_hash
            ),
            None,
        )
        if existing:
            verify_transcript(self.repository, existing)
            return existing
        if not self.repository.claim_run(session.debate_id, session.content_hash):
            raise AgentContextError("DEBATE_ALREADY_CLAIMED_OR_INTERRUPTED")
        memos: dict[AgentRole, AnalystResearchMemo] = {
            AgentRole.BULL: self.repository.get(session.bull_memo_hash, BullResearchMemo),
            AgentRole.BEAR: self.repository.get(session.bear_memo_hash, BearResearchMemo),
        }
        parents = {
            role: self.repository.get(memo.context_hash, AgentRunContext)
            for role, memo in memos.items()
        }
        shared: dict[str, AgentToolResult] = {}
        for context in parents.values():
            run = next(
                r
                for r in self.repository.list(AgentRunRecord)
                if r.context_hash == context.content_hash and r.memo_hash
            )
            for key in run.tool_result_hashes:
                result = self.repository.get(key, AgentToolResult)
                if (
                    result.context_hash != context.content_hash
                    or result.snapshot_hash != session.snapshot_hash
                ):
                    raise AgentContextError("INITIAL_TOOL_LINEAGE_MISMATCH")
                shared[key] = result
        critiques: list[FrozenCritique] = []
        rebuttals: list[FrozenRebuttal] = []
        contexts: dict[AgentRole, AgentRunContext] = {}
        edges = [
            EvidenceGraphEdge(
                created_at=session.created_at,
                agent=role,
                evidence_hash=ref.artifact_hash,
                relation=EvidenceRelation(relation),
            )
            for role, memo in memos.items()
            for refs, relation in (
                (memo.evidence_for, "SUPPORT"),
                (memo.evidence_against, "CONTRADICTION"),
            )
            for ref in refs
        ]
        status, error = DebateStatus.COMPLETE, None
        try:
            for role in AgentRole:
                self._check(session, cancel)
                provider = self.providers.get(role)
                if provider is None or not provider.health().configured:
                    raise AgentProviderError("DEBATE_AGENT_UNAVAILABLE")
                if provider.identity().content_hash != parents[role].model.content_hash:
                    raise AgentContextError("DEBATE_PROVIDER_IDENTITY_MISMATCH")
                contexts[role] = self._context(session, parents[role])
            for role in AgentRole:
                self._check(session, cancel)
                self.repository.audit(
                    "DEBATE_CRITIQUING",
                    run_id=session.debate_id,
                    now=self.clock(),
                    safe_code=role.value,
                )
                other = AgentRole.BEAR if role is AgentRole.BULL else AgentRole.BULL
                context = contexts[role]
                request = self._request(session, context, memos, shared, None)
                started = time.monotonic()
                draft = ProviderRunner(self.providers[role], self.repository).generate(
                    request, CritiqueDraft, cancel=cancel
                )
                self._check(session, cancel)
                if (
                    draft.critic_agent is not role
                    or draft.target_memo_hash != memos[other].content_hash
                ):
                    raise AgentContextError("CRITIQUE_TARGET_MISMATCH")
                self._refs(draft.evidence_refs, shared)
                mandate = (bull_mandate if role is AgentRole.BULL else bear_mandate)(
                    context.created_at
                )
                gateway = AgentToolGateway(self.repository, mandate)
                added = []
                for index, analysis in enumerate(draft.requests):
                    self._check(session, cancel)
                    now = self.clock()
                    result = gateway.execute(
                        context,
                        AgentToolRequest(
                            created_at=now,
                            request_id=f"{context.run_id}:{index}",
                            run_id=context.run_id,
                            context_hash=context.content_hash,
                            snapshot_hash=context.snapshot_hash,
                            tool=analysis.tool,
                            arguments=ToolArguments(
                                created_at=now,
                                security_id=analysis.security_id,
                                analysis_id=analysis.analysis_id,
                                lookback=analysis.lookback,
                            ),
                        ),
                        now=now,
                    )
                    shared[result.content_hash] = result
                    added.append(result.content_hash)
                    edges.append(
                        EvidenceGraphEdge(
                            created_at=now,
                            agent=role,
                            evidence_hash=result.content_hash,
                            relation=EvidenceRelation.REQUESTED,
                        )
                    )
                critique = self.repository.put(
                    FrozenCritique(
                        created_at=self.clock(),
                        debate_id=session.debate_id,
                        snapshot_hash=session.snapshot_hash,
                        context_hash=context.content_hash,
                        prompt_hash=request.prompt_hash(),
                        model_hash=context.model.content_hash,
                        duration_ms=(time.monotonic() - started) * 1000,
                        draft=draft,
                        tool_result_hashes=tuple(added),
                    )
                )
                critiques.append(critique)
                edges.extend(
                    EvidenceGraphEdge(
                        created_at=critique.created_at,
                        agent=role,
                        evidence_hash=key,
                        relation=EvidenceRelation.CRITIQUE_REFERENCE,
                    )
                    for key in draft.evidence_refs
                )
                self.repository.audit(
                    "CRITIQUE_FROZEN",
                    run_id=session.debate_id,
                    now=self.clock(),
                    artifact_hash=critique.content_hash,
                )
            if session.include_rebuttals:
                for role in AgentRole:
                    self._check(session, cancel)
                    self.repository.audit(
                        "DEBATE_REBUTTING",
                        run_id=session.debate_id,
                        now=self.clock(),
                        safe_code=role.value,
                    )
                    opponent = next(c for c in critiques if c.draft.critic_agent is not role)
                    context = contexts[role]
                    request = self._request(session, context, memos, shared, opponent)
                    started = time.monotonic()
                    draft_reply = ProviderRunner(self.providers[role], self.repository).generate(
                        request, RebuttalDraft, cancel=cancel
                    )
                    self._check(session, cancel)
                    if draft_reply.respondent_agent is not role or (
                        draft_reply.target_critique_hash != opponent.content_hash
                    ):
                        raise AgentContextError("REBUTTAL_TARGET_MISMATCH")
                    self._refs(draft_reply.evidence_refs, shared)
                    rebuttals.append(
                        self.repository.put(
                            FrozenRebuttal(
                                created_at=self.clock(),
                                debate_id=session.debate_id,
                                snapshot_hash=session.snapshot_hash,
                                context_hash=context.content_hash,
                                prompt_hash=request.prompt_hash(),
                                model_hash=context.model.content_hash,
                                duration_ms=(time.monotonic() - started) * 1000,
                                draft=draft_reply,
                            )
                        )
                    )
            self._check(session, cancel)
        except AgentError as failure:
            error = str(failure)
            status = DebateStatus.STALE if "STALE" in error else DebateStatus.INCOMPLETE
        except (ValueError, KeyError, StopIteration):
            status, error = DebateStatus.INCOMPLETE, "INVALID_DEBATE_OUTPUT"
        now = self.clock()
        transcript = self.repository.put(
            DebateTranscript(
                created_at=now,
                debate_id=session.debate_id,
                session_hash=session.content_hash,
                protocol_hash=session.protocol_hash,
                boundary_hash=session.boundary_hash,
                snapshot_hash=session.snapshot_hash,
                bull_memo_hash=session.bull_memo_hash,
                bear_memo_hash=session.bear_memo_hash,
                critiques=tuple(c.content_hash for c in critiques),
                rebuttals=tuple(r.content_hash for r in rebuttals),
                evidence_hashes=tuple(sorted(shared)),
                evidence_graph=tuple(edges),
                falsification_checks=checks_from_results(tuple(shared.values()), now),
                started_at=session.created_at,
                completed_at=now,
                status=status,
                error_code=error,
            )
        )
        verify_transcript(self.repository, transcript)
        self.repository.audit(
            "DEBATE_FROZEN",
            run_id=session.debate_id,
            now=now,
            artifact_hash=transcript.content_hash,
            safe_code=error,
        )
        return transcript

    def _check(self, session: DebateSession, cancel: threading.Event | None) -> None:
        now = self.clock()
        if now.tzinfo is None or not session.created_at <= now < session.expires_at:
            raise AgentContextError("STALE_DEBATE")
        if cancel is not None and cancel.is_set():
            raise AgentProviderError("PROVIDER_CANCELLED")
        for key in (session.bull_context_hash, session.bear_context_hash):
            context = self.repository.get(key, AgentRunContext)
            validate_context(self.repository, context, now)
            if _boundary(self.repository, context) != session.boundary_hash:
                raise AgentContextError("DEBATE_EVIDENCE_BOUNDARY_MISMATCH")
        verify_session(self.repository, session)

    def _context(self, session: DebateSession, parent: AgentRunContext) -> AgentRunContext:
        now = session.created_at
        mandate = (bull_mandate if parent.agent.role is AgentRole.BULL else bear_mandate)(now)
        values = parent.model_dump(mode="json", exclude={"content_hash"})
        values.update(
            created_at=now,
            run_id=f"{session.debate_id}:{parent.agent.role}",
            parent_run_id=parent.run_id,
            expires_at=session.expires_at,
            tool_policy_hash=mandate.content_hash,
        )
        agent = parent.agent.model_dump(mode="json", exclude={"content_hash"})
        agent.update(
            created_at=now,
            version=AgentVersion(
                created_at=now,
                version="42.1",
                implementation_version="42-v1",
                prompt_hash=digest(
                    {
                        "system": SYSTEM_SAFETY_POLICY,
                        "mandate": mandate.mandate,
                        "critique": CritiqueDraft.model_json_schema(),
                        "rebuttal": RebuttalDraft.model_json_schema(),
                    }
                ),
            ).model_dump(mode="json"),
        )
        values["agent"] = agent
        return self.repository.put(AgentRunContext.model_validate(values))

    @staticmethod
    def _refs(keys: tuple[str, ...], shared: dict[str, AgentToolResult]) -> None:
        if len(set(keys)) != len(keys) or not set(keys) <= set(shared):
            raise AgentContextError("UNKNOWN_OR_DUPLICATE_DEBATE_REFERENCE")

    def _request(
        self,
        session: DebateSession,
        context: AgentRunContext,
        memos: dict[AgentRole, AnalystResearchMemo],
        shared: dict[str, AgentToolResult],
        critique: FrozenCritique | None,
    ) -> StructuredRequest:
        payload = {
            "initial_memos": {
                role.value: memo.model_dump(mode="json") for role, memo in memos.items()
            },
            "shared_evidence": [
                {
                    "hash": row.content_hash,
                    "tool": row.tool,
                    "status": row.status,
                    "metrics": [
                        m.model_dump(
                            mode="json", exclude={"created_at", "content_hash", "schema_version"}
                        )
                        for m in row.metrics
                    ],
                }
                for row in shared.values()
            ],
            "falsification_routes": list(CHECK_ROUTES),
            "target_critique": critique.model_dump(mode="json") if critique else None,
        }
        evidence = json.dumps(payload, sort_keys=True)
        if len(evidence) > protocol().max_evidence_characters:
            raise AgentProviderError("DEBATE_PROMPT_BUDGET_EXCEEDED")
        mandate = (bull_mandate if context.agent.role is AgentRole.BULL else bear_mandate)(
            context.created_at
        )
        return StructuredRequest(
            run_id=session.debate_id,
            sections=prompt_sections(
                mandate,
                context,
                task=(
                    "One critique of the opponent's frozen memo. Challenge claims and identify "
                    "missing canonical tests. Up to three approved tool requests, shared publicly. "
                    "Interpretations and unsupported arguments are NOT quantitative evidence. "
                    "No peer edits or recursion."
                    if critique is None
                    else "One final rebuttal to this critique. Concede unsupported claims and use "
                    "only published shared evidence hashes. No further tools, turns or execution."
                ),
                untrusted_evidence_json=evidence,
            ),
            schema_json=json.dumps(
                (CritiqueDraft if critique is None else RebuttalDraft).model_json_schema()
            ),
            timeout_seconds=self.timeout_seconds,
            max_output_tokens=2800 if critique is None else 1600,
        )


def verify_session(repository: AgentRepository, session: DebateSession) -> None:
    session.verified()
    for memo_hash, contract, context_hash, role in (
        (session.bull_memo_hash, BullResearchMemo, session.bull_context_hash, AgentRole.BULL),
        (session.bear_memo_hash, BearResearchMemo, session.bear_context_hash, AgentRole.BEAR),
    ):
        memo = repository.get(memo_hash, contract)
        context = repository.get(context_hash, AgentRunContext)
        if (
            memo.context_hash != context_hash
            or memo.agent.role is not role
            or (
                memo.as_of != session.as_of
                or memo.snapshot_hash != session.snapshot_hash
                or memo.created_at > session.created_at
                or session.expires_at > context.expires_at
                or _boundary(repository, context) != session.boundary_hash
            )
        ):
            raise AgentContextError("DEBATE_SESSION_BINDING_MISMATCH")


def verify_transcript(repository: AgentRepository, transcript: DebateTranscript) -> None:
    transcript.verified()
    session = repository.get(transcript.session_hash, DebateSession)
    verify_session(repository, session)
    if transcript.started_at != session.created_at or (
        transcript.status is DebateStatus.COMPLETE
        and (transcript.completed_at >= session.expires_at or transcript.error_code is not None)
    ):
        raise AgentContextError("TRANSCRIPT_CLOCK_OR_STATUS_MISMATCH")
    if any(
        getattr(transcript, field) != getattr(session, field)
        for field in (
            "debate_id",
            "protocol_hash",
            "boundary_hash",
            "snapshot_hash",
            "bull_memo_hash",
            "bear_memo_hash",
        )
    ):
        raise AgentContextError("TRANSCRIPT_SESSION_MISMATCH")
    repository.get(session.bull_memo_hash, BullResearchMemo)
    repository.get(session.bear_memo_hash, BearResearchMemo)
    repository.get(session.protocol_hash, DebateProtocol)
    shared = {key: repository.get(key, AgentToolResult) for key in transcript.evidence_hashes}
    for result in shared.values():
        context = repository.get(result.context_hash, AgentRunContext)
        request = repository.get(result.request_hash, AgentToolRequest)
        if _boundary(repository, context) != session.boundary_hash or (
            request.context_hash != result.context_hash
            or request.run_id != result.run_id
            or result.run_id != context.run_id
            or request.snapshot_hash != result.snapshot_hash
            or request.tool is not result.tool
            or any(metric.available_time > session.as_of for metric in result.metrics)
        ):
            raise AgentContextError("TRANSCRIPT_TOOL_LINEAGE_MISMATCH")
        if result.snapshot_hash != transcript.snapshot_hash:
            raise AgentContextError("TRANSCRIPT_EVIDENCE_MISMATCH")
    if any(
        edge.evidence_hash not in transcript.evidence_hashes for edge in transcript.evidence_graph
    ):
        raise AgentContextError("TRANSCRIPT_GRAPH_REFERENCE_MISMATCH")
    critics = []
    for key in transcript.critiques:
        row = repository.get(key, FrozenCritique)
        context = repository.get(row.context_hash, AgentRunContext)
        _verify_turn_context(repository, session, context)
        critics.append(row.draft.critic_agent)
        target = (
            session.bear_memo_hash
            if row.draft.critic_agent is AgentRole.BULL
            else session.bull_memo_hash
        )
        if (
            row.debate_id != transcript.debate_id
            or row.snapshot_hash != transcript.snapshot_hash
            or (
                row.draft.target_memo_hash != target
                or context.agent.role is not row.draft.critic_agent
                or row.model_hash != context.model.content_hash
                or not set(row.tool_result_hashes) <= set(shared)
                or not session.created_at <= row.created_at <= transcript.completed_at
            )
        ):
            raise AgentContextError("TRANSCRIPT_CRITIQUE_MISMATCH")
        DebateWorker._refs(row.draft.evidence_refs, shared)
    if len(critics) != len(set(critics)):
        raise AgentContextError("DUPLICATE_DEBATE_CRITIC")
    respondents = []
    for key in transcript.rebuttals:
        reply = repository.get(key, FrozenRebuttal)
        context = repository.get(reply.context_hash, AgentRunContext)
        _verify_turn_context(repository, session, context)
        respondents.append(reply.draft.respondent_agent)
        if reply.draft.target_critique_hash not in transcript.critiques or (
            reply.debate_id != transcript.debate_id
            or reply.snapshot_hash != transcript.snapshot_hash
            or reply.model_hash != context.model.content_hash
            or reply.draft.respondent_agent is not context.agent.role
            or not session.created_at <= reply.created_at <= transcript.completed_at
        ):
            raise AgentContextError("TRANSCRIPT_REBUTTAL_MISMATCH")
        target_critique = repository.get(reply.draft.target_critique_hash, FrozenCritique)
        if target_critique.draft.critic_agent is reply.draft.respondent_agent:
            raise AgentContextError("REBUTTAL_OPPONENT_REQUIRED")
        DebateWorker._refs(reply.draft.evidence_refs, shared)
    if len(respondents) != len(set(respondents)):
        raise AgentContextError("DUPLICATE_DEBATE_RESPONDENT")
    if transcript.falsification_checks != checks_from_results(
        tuple(shared.values()), transcript.completed_at
    ):
        raise AgentContextError("TRANSCRIPT_FALSIFICATION_MISMATCH")
    if transcript.status is DebateStatus.COMPLETE and len(transcript.rebuttals) != (
        2 if session.include_rebuttals else 0
    ):
        raise AgentContextError("TRANSCRIPT_COMPLETION_MISMATCH")


def _verify_turn_context(
    repository: AgentRepository,
    session: DebateSession,
    context: AgentRunContext,
) -> None:
    parent_hash = (
        session.bull_context_hash
        if context.agent.role is AgentRole.BULL
        else session.bear_context_hash
    )
    parent = repository.get(parent_hash, AgentRunContext)
    if (
        context.parent_run_id != parent.run_id
        or context.agent.version.implementation_version != "42-v1"
        or (
            _boundary(repository, context) != session.boundary_hash
            or context.created_at != session.created_at
            or context.expires_at != session.expires_at
        )
    ):
        raise AgentContextError("DEBATE_TURN_CONTEXT_MISMATCH")
