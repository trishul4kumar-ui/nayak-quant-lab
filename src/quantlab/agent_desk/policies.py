"""Finite resource budgets for the research desk."""

from datetime import UTC, datetime

from quantlab.agent_desk.models import DailyDeskPolicy, DeskJob, DeskJobType

POLICY_TIME = datetime(2026, 10, 8, tzinfo=UTC)


def default_daily_desk_policy() -> DailyDeskPolicy:
    return DailyDeskPolicy(
        created_at=POLICY_TIME,
        schema_version="daily-desk-v1",
        policy_id="49-v1",
        max_agent_runs_per_interval=4,
        max_concurrent_model_calls=2,
        max_tool_calls_per_run=3,
        max_debate_rounds=1,
        candidate_refresh_cooldown_seconds=300,
        repeated_failure_cooldown_seconds=900,
        maximum_research_jobs_per_tick=4,
    )


def admits_job(
    job: DeskJob,
    *,
    started_this_interval: int,
    running_model_calls: int,
    policy: DailyDeskPolicy,
) -> bool:
    """Admission is deterministic and never dispatches a model call itself."""
    policy = policy.verified()
    if not job.safe_research_read or job.attempt_count >= job.max_attempts:
        return False
    if started_this_interval >= policy.max_agent_runs_per_interval:
        return False
    requires_model = job.job_type in {
        DeskJobType.BULL_SCAN,
        DeskJobType.BEAR_SCAN,
        DeskJobType.DEBATE,
    }
    return not requires_model or running_model_calls < policy.max_concurrent_model_calls
