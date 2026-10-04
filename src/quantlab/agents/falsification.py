"""Named canonical-check routes; missing research inputs never become a passing test."""

from datetime import datetime

from quantlab.agents.contracts import EvidenceStatus
from quantlab.agents.debate_contracts import FalsificationCheck
from quantlab.agents.tool_contracts import AgentToolResult, ToolName

CHECK_ROUTES = (
    ("oos_walk_forward", ToolName.RUN_VALIDATION),
    ("robustness", ToolName.RUN_VALIDATION),
    ("multiple_testing", ToolName.RUN_ECONOMETRICS),
    ("factor_explanation", ToolName.QUERY_FACTOR),
    ("regime_dependence", ToolName.QUERY_REGIME),
    ("cost_resilience", ToolName.RUN_TCA),
    ("liquidity", ToolName.RUN_TCA),
    ("parameter_fragility", ToolName.RUN_VALIDATION),
    ("benchmark_alternatives", ToolName.RUN_BACKTEST),
    ("test_set_integrity", ToolName.RUN_VALIDATION),
)


def checks_from_results(
    results: tuple[AgentToolResult, ...], now: datetime
) -> tuple[FalsificationCheck, ...]:
    checks = []
    for name, tool in CHECK_ROUTES:
        relevant = tuple(
            sorted((row for row in results if row.tool is tool), key=lambda row: row.content_hash)
        )
        metrics = tuple(
            metric
            for row in relevant
            if row.status == "COMPLETED"
            for metric in row.metrics
            if metric.name == name
        )
        statuses = {metric.status for metric in metrics}
        status = next(
            (
                candidate
                for candidate in (
                    EvidenceStatus.FAIL,
                    EvidenceStatus.UNKNOWN,
                    EvidenceStatus.NOT_TESTED,
                    EvidenceStatus.WARN,
                )
                if candidate in statuses
            ),
            EvidenceStatus.PASS if metrics else EvidenceStatus.NOT_TESTED,
        )
        checks.append(
            FalsificationCheck(
                created_at=now,
                name=name,
                canonical_tool=tool,
                result_hashes=tuple(row.content_hash for row in relevant),
                status=status,
                note="Only an exact named canonical check counts. Descriptive exposure/regime "
                "or an agent argument is not OOS, independent edge or falsification validation.",
            )
        )
    return tuple(checks)
