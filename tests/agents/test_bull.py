from __future__ import annotations

import json
import threading
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError
from tests.agents.conftest import NOW

from quantlab.agents.bull import (
    PIPELINE,
    BullWorker,
    create_bull_context,
    search_bull_history,
)
from quantlab.agents.context import FrozenHistory
from quantlab.agents.contracts import (
    AgentModelIdentity,
    AgentRunContext,
    AgentState,
    DataKind,
    EvidenceStatus,
    ResearchMode,
    Stance,
)
from quantlab.agents.errors import AgentContextError
from quantlab.agents.hashing import digest
from quantlab.agents.provider import ProviderHealth, StructuredRequest, UnavailableProvider
from quantlab.agents.repository import AgentRepository
from quantlab.agents.research import (
    BullMemoDraft,
    BullResearchMemo,
    CheckQuestion,
    ResearchScreen,
    ResearchTransition,
)
from quantlab.agents.tool_contracts import AgentToolResult
from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.domain.models import OHLCVBar
from quantlab.realtime_data.freeze import freeze
from quantlab.realtime_data.mock import seed_observations


def snapshot():
    rows = seed_observations()
    return freeze(rows, as_of=max(row.processing_time for row in rows))


class ResearchFixtureProvider:
    """Test-only provider derives references from the actual supplied result set."""

    def __init__(self, stance: str = "LONG_CANDIDATE", fault: str = "") -> None:
        self.stance, self.fault, self.calls = stance, fault, 0
        self.after_memo = lambda: None
        self.requests: list[StructuredRequest] = []

    def identity(self) -> AgentModelIdentity:
        return AgentModelIdentity(created_at=NOW, provider="fixture", model="test", version="1")

    def health(self) -> ProviderHealth:
        return ProviderHealth(
            provider="fixture", model="test", configured=True, observed_status="FIXTURE_ONLY"
        )

    def generate_structured(self, request: StructuredRequest) -> str:
        self.calls += 1
        self.requests.append(request)
        schema = json.loads(request.schema_json)
        if schema["title"] == "ResearchPlan":
            if self.fault == "live_tool":
                return json.dumps(
                    {
                        "hypothesis": "A falsifiable momentum hypothesis",
                        "rationale": "Slow information diffusion is an untested rationale",
                        "requests": [
                            {
                                "tool": "place_live_order",
                                "analysis_id": None,
                                "security_id": None,
                                "lookback": 20,
                            }
                        ],
                    }
                )
            return json.dumps(
                {
                    "hypothesis": "A falsifiable momentum hypothesis",
                    "rationale": "Slow information diffusion is an untested rationale",
                    "requests": [],
                }
            )
        evidence = json.loads(dict(request.sections)["UNTRUSTED EVIDENCE"])
        context = json.loads(dict(request.sections)["FROZEN CONTEXT SUMMARY"])
        payload = self.memo_payload(context["security_scope"], evidence["results"])
        if self.fault == "foreign_ref":
            payload["evidence_for"] = [digest("not an evidence artifact")]
        if self.fault == "sizing":
            payload["quantity"] = 10
        if self.fault == "order_price":
            payload["order_price"] = 100
        if self.fault == "instruction_price":
            payload["hypothesis"] = "Entry: 100 INR is the recommended broker order price"
        self.after_memo()
        return json.dumps(payload)

    def continue_structured(self, request: StructuredRequest) -> str:
        return self.generate_structured(request)

    def memo_payload(self, scope: list[str], results: list[dict]) -> dict:
        return {
            "security_scope": scope,
            "horizon": "several sessions",
            "hypothesis": "Momentum continuation may persist until market participation weakens",
            "economic_rationale": "Slow information diffusion could explain persistence; "
            "unvalidated",
            "evidence_for": [results[1]["hash"]],
            "evidence_against": [results[-1]["hash"]],
            "invalidation_conditions": [
                "Reject if OOS evidence contradicts the thesis",
                "Reject if estimated trading costs consume the effect",
            ],
            "stance": self.stance,
            "entry": "MOMENTUM_CONTINUATION",
            "exit": "THESIS_INVALIDATION",
            "raw_confidence": 0.6,
            "uncertainties": ["Model and out-of-sample support have not been established"],
            "answers": [
                {
                    "question": question.value,
                    "answer": "Evidence remains incomplete; request the relevant canonical test",
                }
                for question in CheckQuestion
            ],
            "no_trade_reason": "Required empirical validation is missing"
            if self.stance == "NO_TRADE"
            else None,
        }


def make_context(
    repository: AgentRepository, provider: ResearchFixtureProvider, with_history: bool = False
) -> AgentRunContext:
    snap = snapshot()
    history = None
    if with_history:
        bars = []
        for index, name in enumerate(sorted({row.security_id for row in snap.observations})):
            price = 100.0 + index * 10
            for offset in range(30):
                at = snap.as_of - timedelta(days=29 - offset)
                price *= 1 + 0.002 + 0.0005 * ((offset % 5) - 2) + index * 0.0001
                bars.append(
                    OHLCVBar(
                        instrument=InstrumentId.parse(name),
                        pit=PointInTime(
                            event_time=at, available_time=at, effective_time=at, ingestion_time=at
                        ),
                        open=price,
                        high=price,
                        low=price,
                        close=price,
                        volume=1000,
                        price_kind="raw_price",
                        data_kind="synthetic",
                    )
                )
        history = FrozenHistory(
            created_at=NOW,
            snapshot_hash=snap.snapshot_hash,
            bars_json=tuple(bar.model_dump_json() for bar in bars),
            price_basis="raw_price",
            data_kind=DataKind.SYNTHETIC,
        )
    return create_bull_context(
        repository, snap, provider, now=NOW, history=history, mode=ResearchMode.REPLAY
    )


def test_bull_pipeline_and_unvalidated_long_downgrade(repository: AgentRepository) -> None:
    provider = ResearchFixtureProvider()
    context = make_context(repository, provider, with_history=True)
    run = BullWorker(repository, provider, clock=lambda: NOW).run(context)
    assert run.state is AgentState.FROZEN and run.memo_hash
    memo = repository.get(run.memo_hash, BullResearchMemo)
    assert memo.stance is Stance.MORE_RESEARCH
    assert memo.validation is EvidenceStatus.NOT_TESTED
    assert memo.preferred_entry_archetype == "MORE_RESEARCH"
    assert memo.calibrated_confidence is None and memo.outcome_status == "NOT_TESTED"
    assert [row.state for row in repository.list(ResearchTransition)] == [
        *PIPELINE,
        AgentState.FROZEN,
    ]
    assert provider.calls == 2 and len(run.tool_result_hashes) == 9
    assert all(len(dict(req.sections)["UNTRUSTED EVIDENCE"]) <= 24000 for req in provider.requests)
    assert [req.max_output_tokens for req in provider.requests] == [1000, 2400]
    factor = next(row for row in memo.evidence_sections if row.name == "factor")
    assert factor.status is EvidenceStatus.PASS
    assert any("exposure may explain returns" in row.description for row in memo.uncertainties)
    for ref in (*memo.evidence_for, *memo.evidence_against):
        result = repository.get(ref.artifact_hash, AgentToolResult)
        assert result.context_hash == context.content_hash
    assert memo.self_falsification and len(memo.thesis.invalidation_conditions) >= 2
    screen = repository.get(memo.screen_hash, ResearchScreen)
    assert len(screen.research_queue) == len(context.security_scope)


def test_no_trade_is_successful_and_restart_preserves_memo(tmp_path: Path) -> None:
    path = tmp_path / "bull.sqlite"
    repository = AgentRepository(path)
    provider = ResearchFixtureProvider("NO_TRADE")
    context = make_context(repository, provider)
    run = BullWorker(repository, provider, clock=lambda: NOW).run(context)
    assert run.state is AgentState.NO_TRADE and run.memo_hash
    memo = repository.get(run.memo_hash, BullResearchMemo)
    repository.close()
    repository = AgentRepository(path)
    try:
        assert repository.get(run.memo_hash, BullResearchMemo) == memo
        assert search_bull_history(repository, "empirical") == (memo,)
        assert search_bull_history(repository, as_of=context.as_of) == ()
        assert BullWorker(repository, provider, clock=lambda: NOW).run(context) == run
        assert provider.calls == 2
    finally:
        repository.close()


@pytest.mark.parametrize(
    "fault", ["foreign_ref", "sizing", "order_price", "instruction_price", "live_tool"]
)
def test_provider_cannot_bypass_research_boundary(repository: AgentRepository, fault: str) -> None:
    provider = ResearchFixtureProvider(fault=fault)
    context = make_context(repository, provider)
    run = BullWorker(repository, provider, clock=lambda: NOW).run(context)
    assert run.state is AgentState.ERROR and run.memo_hash is None
    assert not repository.list(BullResearchMemo)


def test_clock_expiry_after_model_response_blocks_freeze(repository: AgentRepository) -> None:
    provider = ResearchFixtureProvider()
    context = make_context(repository, provider)
    clock = [NOW]
    provider.after_memo = lambda: clock.__setitem__(0, context.expires_at)
    run = BullWorker(repository, provider, clock=lambda: clock[0]).run(context)
    assert run.state is AgentState.STALE and run.memo_hash is None
    assert not repository.list(BullResearchMemo)


def test_unavailable_provider_and_cancel_are_explicit(repository: AgentRepository) -> None:
    provider = UnavailableProvider()
    context = create_bull_context(
        repository, snapshot(), provider, now=NOW, mode=ResearchMode.REPLAY
    )
    run = BullWorker(repository, provider, clock=lambda: NOW).run(context)
    assert run.state is AgentState.BLOCKED and run.error_code == "PROVIDER_NOT_CONFIGURED"
    fixture = ResearchFixtureProvider()
    context = make_context(repository, fixture)
    cancel = threading.Event()
    cancel.set()
    assert (
        BullWorker(repository, fixture, clock=lambda: NOW).run(context, cancel=cancel).memo_hash
        is None
    )
    assert fixture.calls == 0


def test_durable_claim_prevents_cross_process_replay(repository: AgentRepository) -> None:
    provider = ResearchFixtureProvider()
    context = make_context(repository, provider)
    assert repository.claim_run(context.run_id, context.content_hash)
    other = AgentRepository(repository.store.path)
    try:
        with pytest.raises(AgentContextError, match="CLAIMED_OR_INTERRUPTED"):
            BullWorker(other, provider, clock=lambda: NOW).run(context)
        assert provider.calls == 0
    finally:
        other.close()


def test_actionable_draft_requires_explicit_falsification() -> None:
    provider = ResearchFixtureProvider()
    payload = provider.memo_payload(["NSE:TCS"], [{"hash": digest("a")}, {"hash": digest("b")}])
    payload["invalidation_conditions"] = []
    with pytest.raises(ValidationError):
        BullMemoDraft.model_validate(payload)


def test_repeat_fixture_screen_is_reproducible(repository: AgentRepository) -> None:
    provider = ResearchFixtureProvider()
    memos = []
    for _ in range(2):
        context = make_context(repository, provider, with_history=True)
        run = BullWorker(repository, provider, clock=lambda: NOW).run(context)
        memos.append(repository.get(run.memo_hash, BullResearchMemo))
    assert memos[0].thesis == memos[1].thesis
    assert memos[0].stance == memos[1].stance
    assert (
        repository.get(memos[0].screen_hash, ResearchScreen).research_queue
        == repository.get(memos[1].screen_hash, ResearchScreen).research_queue
    )


def test_future_effective_history_cannot_enter_bull_context(repository: AgentRepository) -> None:
    provider = ResearchFixtureProvider()
    context = make_context(repository, provider, with_history=True)
    history = repository.get(context.history_hash, FrozenHistory)
    bars = history.bars()
    changed = bars[0].model_dump(mode="json")
    changed["pit"]["effective_time"] = (snapshot().as_of + timedelta(days=1)).isoformat()
    payload = history.model_dump(mode="json", exclude={"content_hash"})
    payload["bars_json"] = [
        OHLCVBar.model_validate(changed).model_dump_json(),
        *history.bars_json[1:],
    ]
    future = FrozenHistory.model_validate(payload)
    with pytest.raises(AgentContextError, match="INVALID_HISTORY_BOUNDARY"):
        create_bull_context(
            repository, snapshot(), provider, now=NOW, history=future, mode=ResearchMode.REPLAY
        )
