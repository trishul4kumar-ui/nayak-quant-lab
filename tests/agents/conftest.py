from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from quantlab.agents.context import create_context
from quantlab.agents.contracts import AgentModelIdentity, AgentRole, AgentRunContext, ResearchMode
from quantlab.agents.permissions import mandate_for
from quantlab.agents.repository import AgentRepository
from quantlab.realtime_data.freeze import freeze
from quantlab.realtime_data.mock import seed_observations

NOW = datetime(2026, 10, 4, 6, tzinfo=UTC)


@pytest.fixture
def repository(tmp_path: Path) -> AgentRepository:
    repo = AgentRepository(tmp_path / "agents.sqlite")
    yield repo
    repo.close()


@pytest.fixture
def context(repository: AgentRepository) -> AgentRunContext:
    observations = seed_observations()
    snap = freeze(observations, as_of=max(row.processing_time for row in observations))
    return create_context(
        repository,
        snap,
        mandate=mandate_for(AgentRole.BULL, created_at=NOW),
        model=AgentModelIdentity(created_at=NOW, provider="fixture", model="test", version="1"),
        now=NOW,
        mode=ResearchMode.REPLAY,
    )
