from __future__ import annotations

from dataclasses import replace

import pytest
from tests.agents.test_foundation import FakeProvider, Output, structured_request

from quantlab.agents.errors import AgentProviderError
from quantlab.agents.provider import (
    MAX_OUTPUT_TOKENS_PER_ATTEMPT,
    MAX_REQUEST_CHARACTERS,
    ProviderRunner,
    StructuredRequest,
)
from quantlab.agents.repository import AgentRepository


@pytest.mark.parametrize("value", [0, -1, MAX_OUTPUT_TOKENS_PER_ATTEMPT + 1, True, 2.5])
def test_invalid_output_caps_never_reach_provider(
    repository: AgentRepository, value: object
) -> None:
    provider = FakeProvider(('{"answer":"ok"}',))
    request = replace(structured_request(), max_output_tokens=value)  # type: ignore[arg-type]
    with pytest.raises(AgentProviderError, match="INVALID_PROVIDER_BUDGET"):
        ProviderRunner(provider, repository).generate(request, Output)
    assert provider.calls == 0
    assert not repository.audit_events()


@pytest.mark.parametrize("retries", [-1, 3, True, 1.5])
def test_invalid_retry_caps_never_reach_provider(
    repository: AgentRepository, retries: object
) -> None:
    provider = FakeProvider(('{"answer":"ok"}',))
    with pytest.raises(AgentProviderError, match="INVALID_PROVIDER_BUDGET"):
        ProviderRunner(provider, repository).generate(
            structured_request(), Output, schema_retries=retries  # type: ignore[arg-type]
        )
    assert provider.calls == 0


def test_oversized_request_rejected_before_transport(repository: AgentRepository) -> None:
    provider = FakeProvider(('{"answer":"ok"}',))
    request = replace(structured_request(), sections=(("evidence", "x" * MAX_REQUEST_CHARACTERS),))
    with pytest.raises(AgentProviderError, match="INVALID_PROVIDER_BUDGET"):
        ProviderRunner(provider, repository).generate(request, Output)
    assert provider.calls == 0


def test_each_schema_retry_records_requested_output_cap(repository: AgentRepository) -> None:
    provider = FakeProvider(("{", '{"answer":"ok"}'))
    request: StructuredRequest = replace(structured_request(), max_output_tokens=123)
    assert ProviderRunner(provider, repository).generate(request, Output).answer == "ok"
    attempts = [event for event in repository.audit_events() if event.event == "PROVIDER_REQUESTED"]
    assert len(attempts) == 2
    assert all(event.safe_code == "OUTPUT_TOKEN_CAP_123" for event in attempts)
    assert all(event.artifact_hash == request.prompt_hash() for event in attempts)
