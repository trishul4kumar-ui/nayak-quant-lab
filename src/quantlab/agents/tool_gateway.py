"""A finite, typed gateway. Only host code can install adapters."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from threading import RLock

from quantlab.agents.canonical_tools import factor_metrics, regime_metrics
from quantlab.agents.context import FrozenHistory, FrozenSnapshot, validate_context
from quantlab.agents.contracts import AgentMandate, AgentRunContext, EvidenceMetric, EvidenceStatus
from quantlab.agents.errors import AgentContextError, AgentPermissionError
from quantlab.agents.permissions import allows
from quantlab.agents.repository import AgentRepository
from quantlab.agents.tool_contracts import (
    TOOL_CAPABILITIES,
    AgentToolRequest,
    AgentToolResult,
    ToolName,
)
from quantlab.core.errors import QuantLabError
from quantlab.data.fabric.types import FeatureStatus
from quantlab.features.definition import (
    FeatureDefinition,
    FeatureFamily,
    FeatureOperator,
    MissingValuePolicy,
)
from quantlab.features.engine import compute_value

ToolAdapter = Callable[[AgentRunContext, AgentToolRequest], tuple[EvidenceMetric, ...]]


class AgentToolGateway:
    def __init__(self, repository: AgentRepository, mandate: AgentMandate) -> None:
        self.repository = repository
        self.mandate = mandate.verified()
        self._lock = RLock()
        self._adapters: dict[ToolName, ToolAdapter] = {
            ToolName.FREEZE_SNAPSHOT: self._market,
            ToolName.INSPECT_MARKET: self._market,
            ToolName.QUERY_FEATURE: self._feature,
            ToolName.QUERY_FACTOR: lambda context, request: factor_metrics(
                repository, context, request
            ),
            ToolName.QUERY_REGIME: lambda context, request: regime_metrics(
                repository, context, request
            ),
        }

    def catalog(self) -> tuple[tuple[str, str, bool], ...]:
        return tuple(
            (tool.value, permission.value, tool in self._adapters)
            for tool, permission in TOOL_CAPABILITIES.items()
        )

    def execute(
        self,
        context: AgentRunContext,
        request: AgentToolRequest,
        *,
        now: datetime,
    ) -> AgentToolResult:
        with self._lock:
            return self._execute(context, request, now=now)

    def _execute(
        self,
        context: AgentRunContext,
        request: AgentToolRequest,
        *,
        now: datetime,
    ) -> AgentToolResult:
        request.verified()
        self.repository.audit(
            "TOOL_REQUESTED", run_id=context.run_id, now=now, artifact_hash=request.content_hash
        )
        permission = TOOL_CAPABILITIES[request.tool]
        if context.tool_policy_hash != self.mandate.content_hash or not allows(
            self.mandate, permission
        ):
            self.repository.audit(
                "TOOL_DENIED", run_id=context.run_id, now=now, safe_code="PERMISSION_DENIED"
            )
            raise AgentPermissionError("PERMISSION_DENIED")
        validate_context(self.repository, context, now)
        if (
            request.run_id != context.run_id
            or request.context_hash != context.content_hash
            or request.snapshot_hash != context.snapshot_hash
            or context.agent.role is not self.mandate.role
        ):
            self.repository.audit(
                "TOOL_DENIED", run_id=context.run_id, now=now, safe_code="SNAPSHOT_BINDING_MISMATCH"
            )
            raise AgentContextError("SNAPSHOT_BINDING_MISMATCH")
        if (
            request.arguments.security_id
            and request.arguments.security_id not in context.security_scope
        ):
            raise AgentContextError("SECURITY_OUT_OF_SCOPE")
        # Count attempts durably, including failed/denied attempts, across process restarts.
        count = sum(
            event.event == "TOOL_REQUESTED"
            for event in self.repository.audit_events(context.run_id)
        )
        if count > self.mandate.max_tool_calls:
            self.repository.audit(
                "TOOL_DENIED", run_id=context.run_id, now=now, safe_code="TOOL_BUDGET_EXHAUSTED"
            )
            raise AgentPermissionError("TOOL_BUDGET_EXHAUSTED")
        cached = next(
            (
                row
                for row in self.repository.list(AgentToolResult)
                if row.request_hash == request.content_hash
            ),
            None,
        )
        if cached is not None:
            return cached
        self.repository.put(request)
        self.repository.audit(
            "TOOL_ALLOWED", run_id=context.run_id, now=now, artifact_hash=request.content_hash
        )
        adapter = self._adapters.get(request.tool)
        status, error = "COMPLETED", None
        metrics: tuple[EvidenceMetric, ...] = ()
        if adapter is None:
            status, error = "UNAVAILABLE", "CANONICAL_ADAPTER_NOT_BOUND"
        else:
            try:
                metrics = adapter(context, request)
            except (ValueError, KeyError, RuntimeError, QuantLabError):
                status, error = "FAILED", "CANONICAL_ENGINE_FAILED"
        if any(row.available_time > context.as_of for row in metrics):
            raise AgentContextError("FUTURE_TOOL_EVIDENCE")
        result = self.repository.put(
            AgentToolResult(
                created_at=now,
                request_hash=request.content_hash,
                run_id=context.run_id,
                context_hash=context.content_hash,
                snapshot_hash=context.snapshot_hash,
                tool=request.tool,
                status=status,
                error_code=error,
                metrics=metrics,
            )
        )
        self.repository.audit(
            "TOOL_COMPLETED",
            run_id=context.run_id,
            now=now,
            artifact_hash=result.content_hash,
            safe_code=error,
        )
        return result

    def _market(
        self,
        context: AgentRunContext,
        request: AgentToolRequest,
    ) -> tuple[EvidenceMetric, ...]:
        snapshot = self.repository.get(context.snapshot_artifact_hash, FrozenSnapshot).snapshot()
        rows: list[EvidenceMetric] = []
        for observation in snapshot.observations:
            if (
                request.arguments.security_id
                and observation.security_id != request.arguments.security_id
            ):
                continue
            rows.append(
                EvidenceMetric(
                    created_at=context.created_at,
                    name="last_observed_price",
                    security_id=observation.security_id,
                    value=observation.price,
                    unit="INR",
                    available_time=observation.receive_time,
                    status=EvidenceStatus.PASS if observation.price else EvidenceStatus.UNKNOWN,
                    note="Observation only; no validated predictive edge or sizing authority.",
                )
            )
        return tuple(rows)

    def _feature(
        self,
        context: AgentRunContext,
        request: AgentToolRequest,
    ) -> tuple[EvidenceMetric, ...]:
        if context.history_hash is None:
            return (
                EvidenceMetric(
                    created_at=context.created_at,
                    name="history_required",
                    available_time=context.as_of,
                    status=EvidenceStatus.NOT_TESTED,
                    note="Snapshot quotes cannot substitute for a PIT historical frame.",
                ),
            )
        history = self.repository.get(context.history_hash, FrozenHistory)
        bars = history.bars()
        feature_id = request.arguments.analysis_id or "momentum"
        operators = {
            "momentum": FeatureOperator.TRAILING_RETURN,
            "volatility": FeatureOperator.ROLLING_STD,
            "distance_from_mean": FeatureOperator.DISTANCE_FROM_MEAN,
        }
        definition = FeatureDefinition(
            feature_id=feature_id,
            version="agents-v1",
            name=feature_id,
            mathematical_definition=operators[feature_id].value,
            inputs=["close"],
            lookback=request.arguments.lookback,
            operator=operators[feature_id],
            family=FeatureFamily.MOMENTUM,
            family_id="desk-trailing",
            missing_value_policy=MissingValuePolicy.NOT_AVAILABLE,
        )
        metrics: list[EvidenceMetric] = []
        for name in context.security_scope:
            if request.arguments.security_id and name != request.arguments.security_id:
                continue
            observation = compute_value(
                definition,
                [row for row in bars if str(row.instrument) == name],
                context.as_of,
            )
            metrics.append(
                EvidenceMetric(
                    created_at=context.created_at,
                    name=feature_id,
                    security_id=name,
                    value=observation.value,
                    available_time=observation.available_time,
                    status=(
                        EvidenceStatus.PASS
                        if observation.status is FeatureStatus.READY
                        else EvidenceStatus.NOT_TESTED
                    ),
                    note=observation.note,
                )
            )
        return tuple(metrics)
