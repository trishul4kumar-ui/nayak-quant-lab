"""Persistent, bounded long-side research worker. No execution imports or authority."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime

from quantlab.agents.context import FrozenHistory, create_context, validate_context
from quantlab.agents.contracts import (
    AgentMandate,
    AgentRole,
    AgentRunContext,
    AgentRunRecord,
    AgentState,
    AgentUncertainty,
    AgentVersion,
    EvidenceReference,
    EvidenceStatus,
    ResearchMode,
    ResearchThesis,
    Stance,
)
from quantlab.agents.errors import AgentContextError, AgentError, AgentProviderError
from quantlab.agents.hashing import digest
from quantlab.agents.permissions import DEFAULT_RESEARCH_CAPABILITIES
from quantlab.agents.prompts import SYSTEM_SAFETY_POLICY, prompt_sections
from quantlab.agents.provider import AgentModelProvider, ProviderRunner, StructuredRequest
from quantlab.agents.repository import AgentRepository
from quantlab.agents.research import (
    BullMemoDraft,
    BullResearchMemo,
    EntryArchetype,
    EvidenceSection,
    FrozenResearchPlan,
    ResearchPlan,
    ResearchScreen,
    ResearchTransition,
)
from quantlab.agents.tool_contracts import (
    AgentToolRequest,
    AgentToolResult,
    ToolArguments,
    ToolName,
)
from quantlab.agents.tool_gateway import AgentToolGateway
from quantlab.ai.permissions import AiCapability
from quantlab.realtime_data.models import RealTimeSnapshot

BULL_MANDATE = (
    "Investigate long-side momentum, continuation, relative strength, breakouts and pullbacks, "
    "breadth, factor exposure, regime, volatility, liquidity, model/ensemble support and approved "
    "catalysts. Seek contradictions and explicit invalidation. Explain beta/factor exposure, "
    "cost survival, OOS/walk-forward, regime dependence and missing data. An evidence gap is "
    "NOT_TESTED, not PASS. NO_TRADE is successful research. No sizing or order prices."
)
MANDATORY = (
    ("factor", ToolName.QUERY_FACTOR),
    ("regime", ToolName.QUERY_REGIME),
    ("statistics", ToolName.RUN_ECONOMETRICS),
    ("model", ToolName.RUN_MODEL_EVALUATION),
    ("ensemble", ToolName.RUN_ENSEMBLE_EVALUATION),
    ("validation", ToolName.RUN_VALIDATION),
    ("liquidity_tca", ToolName.RUN_TCA),
)
PIPELINE = (
    AgentState.IDLE,
    AgentState.OBSERVING,
    AgentState.SCREENING,
    AgentState.FORMING_HYPOTHESIS,
    AgentState.REQUESTING_EVIDENCE,
    AgentState.ANALYZING,
    AgentState.SELF_FALSIFYING,
    AgentState.WRITING_MEMO,
)


def bull_mandate(now: datetime) -> AgentMandate:
    return AgentMandate(
        created_at=now,
        role=AgentRole.BULL,
        mandate=BULL_MANDATE,
        granted=DEFAULT_RESEARCH_CAPABILITIES
        | frozenset(
            {
                AiCapability.RUN_ECONOMETRICS,
                AiCapability.RUN_MODEL_EVALUATION,
                AiCapability.RUN_ENSEMBLE_EVALUATION,
            }
        ),
    )


def create_bull_context(
    repository: AgentRepository,
    snapshot: RealTimeSnapshot,
    provider: AgentModelProvider,
    *,
    now: datetime,
    history: FrozenHistory | None = None,
    mode: ResearchMode = ResearchMode.RESEARCH,
) -> AgentRunContext:
    if len({row.security_id for row in snapshot.observations}) > 20:
        raise AgentContextError("RESEARCH_SCOPE_BUDGET_EXCEEDED")
    if history is not None and len(history.bars_json) > 5040:
        raise AgentContextError("HISTORY_BUDGET_EXCEEDED")
    mandate = bull_mandate(now)
    version = AgentVersion(
        created_at=now,
        version="40.1",
        implementation_version="40-v1",
        prompt_hash=digest(
            {
                "system": SYSTEM_SAFETY_POLICY,
                "mandate": mandate.mandate,
                "plan": ResearchPlan.model_json_schema(),
                "memo": BullMemoDraft.model_json_schema(),
            }
        ),
    )
    return create_context(
        repository,
        snapshot,
        mandate=mandate,
        model=provider.identity(),
        now=now,
        mode=mode,
        history=history,
        agent_version=version,
    )


def search_bull_history(
    repository: AgentRepository,
    query: str = "",
    *,
    as_of: datetime | None = None,
) -> tuple[BullResearchMemo, ...]:
    needle = query.strip().casefold()
    return tuple(
        memo
        for memo in repository.list(BullResearchMemo)
        if (as_of is None or memo.created_at <= as_of)
        and (not needle or needle in memo.model_dump_json().casefold())
    )


def evidence_status(result: AgentToolResult) -> EvidenceStatus:
    if result.status != "COMPLETED" or not result.metrics:
        return EvidenceStatus.NOT_TESTED
    statuses = {metric.status for metric in result.metrics}
    for status in (
        EvidenceStatus.FAIL,
        EvidenceStatus.UNKNOWN,
        EvidenceStatus.NOT_TESTED,
        EvidenceStatus.WARN,
    ):
        if status in statuses:
            return status
    return EvidenceStatus.PASS


class BullWorker:
    def __init__(
        self,
        repository: AgentRepository,
        provider: AgentModelProvider,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.repository, self.provider, self.clock = repository, provider, clock

    def run(
        self,
        context: AgentRunContext,
        *,
        cancel: threading.Event | None = None,
    ) -> AgentRunRecord:
        validate_context(self.repository, context, self.clock())
        if context.agent.role is not AgentRole.BULL:
            raise AgentContextError("BULL_ROLE_REQUIRED")
        mandate = bull_mandate(context.created_at)
        if context.tool_policy_hash != mandate.content_hash or (
            context.agent.version.implementation_version != "40-v1"
            or context.model.content_hash != self.provider.identity().content_hash
        ):
            raise AgentContextError("BULL_IDENTITY_OR_POLICY_MISMATCH")
        existing = next(
            (row for row in self.repository.list(AgentRunRecord) if row.run_id == context.run_id),
            None,
        )
        if existing is not None:
            if existing.context_hash != context.content_hash:
                raise AgentContextError("RUN_IDENTITY_COLLISION")
            if existing.memo_hash is not None:
                cached_memo = self.repository.get(existing.memo_hash, BullResearchMemo)
                if (
                    cached_memo.context_hash != context.content_hash
                    or cached_memo.snapshot_hash != context.snapshot_hash
                ):
                    raise AgentContextError("CACHED_MEMO_BINDING_MISMATCH")
            return existing
        if not self.repository.claim_run(context.run_id, context.content_hash):
            raise AgentContextError("RUN_ALREADY_CLAIMED_OR_INTERRUPTED")
        started = time.monotonic()
        results: list[AgentToolResult] = []
        transitions: list[ResearchTransition] = []
        prompt_hash = context.agent.version.prompt_hash
        gateway = AgentToolGateway(self.repository, mandate)
        runner = ProviderRunner(self.provider, self.repository)

        def check() -> None:
            validate_context(self.repository, context, self.clock())
            if cancel is not None and cancel.is_set():
                raise AgentProviderError("PROVIDER_CANCELLED")

        def transition(state: AgentState, task: str) -> None:
            now = self.clock()
            item = self.repository.put(
                ResearchTransition(
                    created_at=now,
                    run_id=context.run_id,
                    context_hash=context.content_hash,
                    sequence=len(transitions),
                    state=state,
                    task=task,
                    tool_result_hashes=tuple(row.content_hash for row in results),
                )
            )
            transitions.append(item)
            self.repository.audit(
                "STATE_TRANSITION", run_id=context.run_id, now=now, artifact_hash=item.content_hash
            )

        def tool(
            name: ToolName,
            analysis_id: str | None = None,
            security_id: str | None = None,
            lookback: int = 20,
        ) -> AgentToolResult:
            check()
            now = self.clock()
            request = AgentToolRequest(
                created_at=now,
                request_id=f"{context.run_id}:{len(results)}",
                run_id=context.run_id,
                context_hash=context.content_hash,
                snapshot_hash=context.snapshot_hash,
                tool=name,
                arguments=ToolArguments(
                    created_at=now,
                    analysis_id=analysis_id,
                    security_id=security_id,
                    lookback=lookback,
                ),
            )
            result = gateway.execute(context, request, now=now)
            results.append(result)
            return result

        def request(
            task: str,
            contract: type[ResearchPlan] | type[BullMemoDraft],
            plan: ResearchPlan | None = None,
        ) -> StructuredRequest:
            payload = {
                "results": [
                    {
                        "hash": row.content_hash,
                        "tool": row.tool,
                        "status": evidence_status(row),
                        "metrics": [
                            {
                                "name": m.name,
                                "security": m.security_id,
                                "value": m.value,
                                "status": m.status,
                            }
                            for m in row.metrics
                        ],
                        "notes": sorted({m.note for m in row.metrics})[:4],
                    }
                    for row in results
                ],
                "plan": plan.model_dump(mode="json") if plan else None,
                "known_prior_bull_theses": [
                    {
                        "hypothesis": m.thesis.hypothesis,
                        "stance": m.stance,
                        "outcome": m.outcome_status,
                    }
                    for m in search_bull_history(self.repository, as_of=context.as_of)[-5:]
                ],
            }
            evidence = json.dumps(payload, sort_keys=True)
            if len(evidence) > 24000:
                raise AgentProviderError("PROMPT_BUDGET_EXCEEDED")
            return StructuredRequest(
                run_id=context.run_id,
                sections=prompt_sections(
                    mandate, context, task=task, untrusted_evidence_json=evidence
                ),
                schema_json=json.dumps(contract.model_json_schema()),
                timeout_seconds=30,
                max_output_tokens=1000 if plan is None else 2400,
            )

        memo: BullResearchMemo | None = None
        error: str | None = None
        try:
            check()
            transition(AgentState.IDLE, "Research run claimed")
            if not self.provider.health().configured:
                raise AgentProviderError("PROVIDER_NOT_CONFIGURED")
            transition(AgentState.OBSERVING, "Inspect frozen market observations")
            tool(ToolName.INSPECT_MARKET)
            transition(AgentState.SCREENING, "Rank frozen canonical trailing features")
            features = tool(ToolName.QUERY_FEATURE, "momentum")
            ranked = sorted(
                (
                    m
                    for m in features.metrics
                    if m.security_id and m.value is not None and m.status is EvidenceStatus.PASS
                ),
                key=lambda m: (-float(m.value or 0), str(m.security_id)),
            )
            queue = tuple(str(m.security_id) for m in ranked)
            screen = self.repository.put(
                ResearchScreen(
                    created_at=self.clock(),
                    context_hash=context.content_hash,
                    snapshot_hash=context.snapshot_hash,
                    source_result_hash=features.content_hash,
                    research_queue=queue,
                    unranked=tuple(name for name in context.security_scope if name not in queue),
                )
            )
            transition(AgentState.FORMING_HYPOTHESIS, "Form a falsifiable research plan")
            plan_request = request(
                "Propose a falsifiable long-side research hypothesis. "
                "At most three optional typed analyses. Do not repeat the "
                "mandatory factor/regime/statistics/model/ensemble/validation/TCA "
                "analyses, which the host will run regardless.",
                ResearchPlan,
            )
            plan = runner.generate(plan_request, ResearchPlan, cancel=cancel)
            frozen_plan = self.repository.put(
                FrozenResearchPlan(
                    created_at=self.clock(), context_hash=context.content_hash, plan=plan
                )
            )
            transition(AgentState.REQUESTING_EVIDENCE, "Seek support AND disconfirming evidence")
            mandatory_results = {label: tool(name) for label, name in MANDATORY}
            for analysis in plan.requests:
                if analysis.tool in {name for _, name in MANDATORY}:
                    raise AgentContextError("DUPLICATE_MANDATORY_ANALYSIS")
                tool(analysis.tool, analysis.analysis_id, analysis.security_id, analysis.lookback)
            transition(AgentState.ANALYZING, "Review canonical evidence and explicit gaps")
            check()
            transition(AgentState.SELF_FALSIFYING, "Answer all seven adversarial questions")
            memo_request = request(
                "Write a research memo using only these result hashes. "
                "Explicitly answer all seven challenge questions. Missing "
                "validation/cost evidence prevents a trade-ready conclusion. "
                "Entry and exit archetypes only; no numerical execution levels. "
                "History outcomes are NOT_TESTED, never invented.",
                BullMemoDraft,
                plan,
            )
            prompt_hash = memo_request.prompt_hash()
            draft = runner.generate(memo_request, BullMemoDraft, cancel=cancel)
            check()
            transition(AgentState.WRITING_MEMO, "Verify references and freeze research memo")
            memo = self._freeze(context, draft, screen, frozen_plan, results, mandatory_results)
            terminal = AgentState.NO_TRADE if memo.stance is Stance.NO_TRADE else AgentState.FROZEN
        except AgentError as failure:
            error = str(failure)
            terminal = AgentState.STALE if "STALE" in error else AgentState.BLOCKED
            if error in {
                "INVALID_STRUCTURED_OUTPUT",
                "PROVIDER_FAILED",
                "UNKNOWN_OR_FOREIGN_EVIDENCE_REFERENCE",
                "DUPLICATE_EVIDENCE_REFERENCE",
                "MEMO_SECURITY_OUT_OF_SCOPE",
                "DUPLICATE_MANDATORY_ANALYSIS",
            }:
                terminal = AgentState.ERROR
        except (ValueError, KeyError):
            error, terminal = "INVALID_RESEARCH_OUTPUT", AgentState.ERROR
        transition(terminal, error or "Research memo frozen; no execution authority")
        return self.repository.put(
            AgentRunRecord(
                created_at=self.clock(),
                run_id=context.run_id,
                context_hash=context.content_hash,
                state=terminal,
                prompt_hash=prompt_hash,
                model_hash=context.model.content_hash,
                tool_result_hashes=tuple(row.content_hash for row in results),
                memo_hash=memo.content_hash if memo else None,
                duration_ms=(time.monotonic() - started) * 1000,
                error_code=error,
            )
        )

    def _freeze(
        self,
        context: AgentRunContext,
        draft: BullMemoDraft,
        screen: ResearchScreen,
        plan: FrozenResearchPlan,
        results: list[AgentToolResult],
        mandatory_results: dict[str, AgentToolResult],
    ) -> BullResearchMemo:
        validate_context(self.repository, context, self.clock())
        if not set(draft.security_scope) <= set(context.security_scope):
            raise AgentContextError("MEMO_SECURITY_OUT_OF_SCOPE")
        by_hash = {row.content_hash: row.verified() for row in results}
        now = self.clock()

        def refs(hashes: tuple[str, ...]) -> tuple[EvidenceReference, ...]:
            if len(set(hashes)) != len(hashes):
                raise AgentContextError("DUPLICATE_EVIDENCE_REFERENCE")
            output = []
            for key in hashes:
                row = by_hash.get(key)
                if row is None or row.context_hash != context.content_hash:
                    raise AgentContextError("UNKNOWN_OR_FOREIGN_EVIDENCE_REFERENCE")
                output.append(
                    EvidenceReference(
                        created_at=now,
                        artifact_hash=key,
                        snapshot_hash=context.snapshot_hash,
                        kind=row.tool,
                        status=evidence_status(row),
                        available_time=context.as_of,
                        summary=f"{row.tool}: {evidence_status(row)}; interpretation is unverified",
                    )
                )
            return tuple(output)

        support, against = refs(draft.evidence_for), refs(draft.evidence_against)
        sections = tuple(
            EvidenceSection(
                created_at=now,
                name=label,
                result_hash=row.content_hash,
                status=evidence_status(row),
                note=row.error_code
                or "Canonical tool result; computation is not predictive validation",
            )
            for label, row in (("feature", results[1]), *mandatory_results.items())
        )
        validation = evidence_status(mandatory_results["validation"])
        costs = evidence_status(mandatory_results["liquidity_tca"])
        stance = Stance(draft.stance)
        gaps = [
            f"{item.name}: {item.status}"
            for item in sections
            if item.status is not EvidenceStatus.PASS
        ]
        entry = draft.entry
        if stance is Stance.LONG_CANDIDATE and (
            validation is not EvidenceStatus.PASS or costs is not EvidenceStatus.PASS
        ):
            stance, entry = Stance.MORE_RESEARCH, EntryArchetype.MORE_RESEARCH
        uncertainty = tuple(
            AgentUncertainty(created_at=now, category="agent_opinion", description=text)
            for text in draft.uncertainties
        )
        uncertainty += tuple(
            AgentUncertainty(created_at=now, category="host_evidence_gap", description=text)
            for text in gaps
        )
        uncertainty += (
            AgentUncertainty(
                created_at=now,
                category="factor_explanation",
                description="Market/factor exposure may explain returns. "
                "Equal-weight universe beta "
                "is not NIFTY beta, residual alpha, or validated independent edge.",
            ),
        )
        validate_context(self.repository, context, self.clock())
        return self.repository.put(
            BullResearchMemo(
                created_at=now,
                thesis_id="bull-"
                + digest({"context": context.content_hash, "hypothesis": draft.hypothesis})[:16],
                context_hash=context.content_hash,
                snapshot_hash=context.snapshot_hash,
                as_of=context.as_of,
                agent=context.agent,
                model_hash=context.model.content_hash,
                security_scope=tuple(sorted(set(draft.security_scope))),
                thesis=ResearchThesis(
                    created_at=now,
                    hypothesis=draft.hypothesis,
                    economic_rationale=draft.economic_rationale,
                    invalidation_conditions=draft.invalidation_conditions,
                    horizon=draft.horizon,
                ),
                evidence_for=support,
                evidence_against=against,
                stance=stance,
                requested_analyses=tuple(row.tool.value for row in results),
                preferred_entry_archetype=entry,
                preferred_exit_archetype=draft.exit,
                preferred_exposure="long-side research only",
                raw_confidence=draft.raw_confidence,
                uncertainties=uncertainty,
                validation=validation,
                no_trade_reason=draft.no_trade_reason,
                screen_hash=screen.content_hash,
                plan_hash=plan.content_hash,
                evidence_sections=sections,
                self_falsification=draft.answers,
                data_kind=context.data_kind,
            )
        )
