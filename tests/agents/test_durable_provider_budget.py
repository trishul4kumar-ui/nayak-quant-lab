from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier

import pytest
from tests.agents.test_foundation import FakeProvider, Output, structured_request

from quantlab.agents.errors import AgentProviderError
from quantlab.agents.provider import ProviderRunner
from quantlab.agents.provider_budget import ProviderBudgetPolicy
from quantlab.agents.repository import AgentRepository


def _request(task: str, family: str | None, *, timeout: float = 1.0):  # type: ignore[no-untyped-def]
    return replace(
        structured_request(timeout), run_id=task, budget_family_id=family, max_output_tokens=100
    )


@pytest.mark.parametrize("bad", [0, -1, True, 2.5, 2**63])
def test_invalid_budget_policy_is_rejected(bad: object) -> None:
    with pytest.raises(ValueError, match="positive bounded integers"):
        ProviderBudgetPolicy(bad, 200, 300)  # type: ignore[arg-type]


def test_explicit_required_policy_and_family_cannot_be_omitted(repository: AgentRepository) -> None:
    provider = FakeProvider(('{"answer":"ok"}',))
    with pytest.raises(AgentProviderError, match="POLICY_REQUIRED"):
        ProviderRunner(provider, repository, require_budget=True).generate(
            _request("task", "family"), Output
        )
    ProviderRunner(provider, repository, budget_policy=ProviderBudgetPolicy(100, 200, 300))
    with pytest.raises(AgentProviderError, match="SCOPE_REQUIRED"):
        ProviderRunner(provider, repository).generate(_request("task", None), Output)
    assert provider.calls == 0
    assert not repository.audit_events()


def test_task_family_and_daily_caps_are_independently_enforced(repository: AgentRepository) -> None:
    provider = FakeProvider(('{"answer":"ok"}',))
    runner = ProviderRunner(
        provider, repository, budget_policy=ProviderBudgetPolicy(150, 250, 350)
    )
    assert runner.generate(_request("a", "one"), Output).answer == "ok"
    with pytest.raises(AgentProviderError, match="TASK_EXCEEDED"):
        runner.generate(_request("a", "one"), Output)
    assert runner.generate(_request("b", "one"), Output).answer == "ok"
    with pytest.raises(AgentProviderError, match="FAMILY_EXCEEDED"):
        runner.generate(_request("c", "one"), Output)
    assert runner.generate(_request("d", "two"), Output).answer == "ok"
    with pytest.raises(AgentProviderError, match="DAILY_EXCEEDED"):
        runner.generate(_request("e", "two"), Output)
    assert provider.calls == 3


def test_schema_retry_and_timeout_remain_conservatively_charged(
    repository: AgentRepository,
) -> None:
    policy = ProviderBudgetPolicy(150, 500, 1000)
    invalid = FakeProvider(("{",))
    runner = ProviderRunner(invalid, repository, budget_policy=policy)
    with pytest.raises(AgentProviderError, match="TASK_EXCEEDED"):
        runner.generate(_request("bad-schema", "one"), Output, schema_retries=1)
    assert invalid.calls == 1
    slow = FakeProvider(('{"answer":"late"}',), delay=0.2)
    with pytest.raises(AgentProviderError, match="TIMEOUT"):
        ProviderRunner(slow, repository).generate(_request("timeout", "one", timeout=0.02), Output)
    with pytest.raises(AgentProviderError, match="TASK_EXCEEDED"):
        ProviderRunner(FakeProvider(('{"answer":"ok"}',)), repository).generate(
            _request("timeout", "one"), Output
        )


def test_utc_day_resets_but_task_and_family_are_lifetime_scopes(
    repository: AgentRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    current = [datetime(2024, 1, 1, 23, 59, tzinfo=UTC)]

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[no-untyped-def]
            return current[0]

    monkeypatch.setattr("quantlab.agents.provider_budget.datetime", Clock)
    provider = FakeProvider(('{"answer":"ok"}',))
    runner = ProviderRunner(provider, repository, budget_policy=ProviderBudgetPolicy(100, 100, 100))
    runner.generate(_request("task-a", "family-a"), Output)
    current[0] += timedelta(minutes=2)
    with pytest.raises(AgentProviderError, match="TASK_EXCEEDED"):
        runner.generate(_request("task-a", "family-b"), Output)
    with pytest.raises(AgentProviderError, match="FAMILY_EXCEEDED"):
        runner.generate(_request("task-b", "family-a"), Output)
    assert runner.generate(_request("task-b", "family-b"), Output).answer == "ok"


def test_budget_reservations_survive_restart_and_store_no_raw_prompt(tmp_path: Path) -> None:
    path = tmp_path / "agents.sqlite"
    repo = AgentRepository(path)
    runner = ProviderRunner(
        FakeProvider(('{"answer":"ok"}',)), repo,
        budget_policy=ProviderBudgetPolicy(100, 500, 500),
    )
    request = replace(
        _request("private-task", "private-family"), sections=(("prompt", "private prompt"),)
    )
    runner.generate(request, Output)
    repo.close()
    reopened = AgentRepository(path)
    with pytest.raises(AgentProviderError, match="TASK_EXCEEDED"):
        ProviderRunner(FakeProvider(('{"answer":"ok"}',)), reopened).generate(request, Output)
    with pytest.raises(AgentProviderError, match="POLICY_CONFLICT"):
        ProviderRunner(
            FakeProvider(('{"answer":"ok"}',)), reopened,
            budget_policy=ProviderBudgetPolicy(200, 500, 500),
        )
    reopened.close()
    with sqlite3.connect(path) as connection:
        rows = connection.execute("SELECT * FROM agent_provider_budget_reservations").fetchall()
    rendered = json.dumps(rows)
    assert "private-task" not in rendered
    assert "private-family" not in rendered
    assert "private prompt" not in rendered
    assert len(rows) == 1 and rows[0][-1] == 100


def test_atomic_reservation_across_instances_and_a_new_process(tmp_path: Path) -> None:
    path = tmp_path / "agents.sqlite"
    repositories = [AgentRepository(path) for _ in range(5)]
    ProviderRunner(
        FakeProvider(('{"answer":"ok"}',)), repositories[0],
        budget_policy=ProviderBudgetPolicy(100, 200, 1000),
    )
    barrier = Barrier(len(repositories))

    def run(index: int) -> str:
        provider = FakeProvider(('{"answer":"ok"}',))
        barrier.wait(timeout=5)
        try:
            ProviderRunner(provider, repositories[index]).generate(
                _request(f"task-{index}", "shared-family"), Output, schema_retries=0
            )
            return "ok"
        except AgentProviderError as exc:
            assert provider.calls == 0
            return str(exc)

    with ThreadPoolExecutor(max_workers=len(repositories)) as executor:
        outcomes = list(executor.map(run, range(len(repositories))))
    assert outcomes.count("ok") == 2
    assert outcomes.count("PROVIDER_BUDGET_FAMILY_EXCEEDED") == 3
    for repo in repositories:
        repo.close()

    program = """
import sys
from pathlib import Path
from quantlab.agents.errors import AgentProviderError
from quantlab.agents.provider_budget import ProviderBudgetLedger
from quantlab.agents.repository import AgentRepository
r = AgentRepository(Path(sys.argv[1]))
try:
    ProviderBudgetLedger(r).reserve(task_id='other', family_id='shared-family',
        output_cap=100, prompt_hash='a' * 64, require_policy=True)
except AgentProviderError as exc:
    print(str(exc))
finally:
    r.close()
"""
    result = subprocess.run(
        [sys.executable, "-c", program, str(path)], text=True, capture_output=True,
        env=os.environ.copy(), check=True,
    )
    assert result.stdout.strip() == "PROVIDER_BUDGET_FAMILY_EXCEEDED"


def test_committed_reservation_survives_process_termination(tmp_path: Path) -> None:
    path = tmp_path / "agents.sqlite"
    repository = AgentRepository(path)
    ProviderRunner(
        FakeProvider(('{"answer":"ok"}',)), repository,
        budget_policy=ProviderBudgetPolicy(100, 200, 200),
    )
    repository.close()
    program = """
import os, sys
from pathlib import Path
from quantlab.agents.provider_budget import ProviderBudgetLedger
from quantlab.agents.repository import AgentRepository
r = AgentRepository(Path(sys.argv[1]))
ProviderBudgetLedger(r).reserve(task_id='crashed-task', family_id='family',
    output_cap=100, prompt_hash='a' * 64, require_policy=True)
os._exit(0)
"""
    subprocess.run([sys.executable, "-c", program, str(path)], check=True, env=os.environ.copy())
    reopened = AgentRepository(path)
    with pytest.raises(AgentProviderError, match="TASK_EXCEEDED"):
        ProviderRunner(FakeProvider(('{"answer":"ok"}',)), reopened).generate(
            _request("crashed-task", "family"), Output
        )
    reopened.close()
