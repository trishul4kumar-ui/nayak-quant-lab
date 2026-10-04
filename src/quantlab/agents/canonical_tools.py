"""PIT adapters to existing factor/regime engines; no parallel quant math."""

from __future__ import annotations

from quantlab.agents.context import FrozenHistory
from quantlab.agents.contracts import AgentRunContext, EvidenceMetric, EvidenceStatus
from quantlab.agents.repository import AgentRepository
from quantlab.agents.tool_contracts import AgentToolRequest
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.factors.market import rolling_betas
from quantlab.regimes.snapshot import compute_snapshot


def history_bars(
    repository: AgentRepository,
    context: AgentRunContext,
) -> dict[InstrumentId, list[OHLCVBar]]:
    if context.history_hash is None:
        return {}
    history = repository.get(context.history_hash, FrozenHistory)
    grouped: dict[InstrumentId, list[OHLCVBar]] = {}
    for bar in history.bars():
        grouped.setdefault(bar.instrument, []).append(bar)
    return grouped


def metric(
    context: AgentRunContext,
    name: str,
    value: float | None,
    note: str,
    security_id: str | None = None,
) -> EvidenceMetric:
    return EvidenceMetric(
        created_at=context.created_at,
        name=name,
        value=value,
        security_id=security_id,
        available_time=context.as_of,
        status=EvidenceStatus.PASS if value is not None else EvidenceStatus.NOT_TESTED,
        note=note,
    )


def factor_metrics(
    repository: AgentRepository,
    context: AgentRunContext,
    request: AgentToolRequest,
) -> tuple[EvidenceMetric, ...]:
    if request.arguments.analysis_id not in {None, "beta", "equal_weight_universe_beta"}:
        raise ValueError("UNMAPPED_FACTOR_ANALYSIS")
    bars = history_bars(repository, context)
    if not bars:
        return (metric(context, "beta", None, "PIT history required; factor exposure unknown."),)
    report = rolling_betas(bars, context.as_of, lookback=request.arguments.lookback)
    note = report.note + "; market/factor exposure may explain returns, not independent alpha."
    return tuple(
        metric(context, "equal_weight_universe_beta", report.betas.get(name), note, name)
        for name in context.security_scope
        if request.arguments.security_id in {None, name}
    )


def regime_metrics(
    repository: AgentRepository,
    context: AgentRunContext,
    request: AgentToolRequest,
) -> tuple[EvidenceMetric, ...]:
    if request.arguments.analysis_id not in {None, "market_state", "descriptive_state"}:
        raise ValueError("UNMAPPED_REGIME_ANALYSIS")
    bars = history_bars(repository, context)
    if not bars:
        return (metric(context, "regime", None, "PIT history required; regime unknown."),)
    report = compute_snapshot(bars, context.as_of, lookback=request.arguments.lookback)
    return tuple(
        metric(context, name, value, report.note + " Missing: " + ", ".join(report.missing))
        for name, value in report.vector().items()
    )
