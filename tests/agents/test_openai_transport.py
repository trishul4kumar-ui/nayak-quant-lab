from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import BaseModel, SecretStr

from quantlab.agents.errors import AgentProviderError
from quantlab.agents.provider import OpenAIResponsesProvider, ProviderRunner, StructuredRequest
from quantlab.agents.repository import AgentRepository


def request() -> StructuredRequest:
    return StructuredRequest(
        run_id="transport",
        sections=(("SYSTEM", "Research only"),),
        schema_json='{"type":"object","properties":{}}',
    )


class Reply:
    def __init__(self, body: object) -> None:
        self.body = body

    def read(self, size: int) -> bytes:
        return json.dumps(self.body).encode()


@contextmanager
def transport(body: object) -> Any:
    with patch("urllib.request.urlopen") as call:
        call.return_value.__enter__.return_value = Reply(body)
        yield call


def test_credentials_not_in_request_body_or_identity_and_health_not_assumed() -> None:
    provider = OpenAIResponsesProvider("configured-model", SecretStr("fixture-credential"))
    assert provider.health().observed_status == "NOT_TESTED"
    body = {
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": '{"answer":"safe"}'},
                ],
            }
        ],
    }
    with transport(body) as call:
        assert provider.generate_structured(request()) == '{"answer":"safe"}'
        sent = call.call_args.args[0]
        assert sent.full_url == "https://api.openai.com/v1/responses"
        payload = sent.data.decode()
        assert "fixture-credential" not in payload
        assert json.loads(payload)["store"] is False
    assert "fixture-credential" not in provider.identity().model_dump_json()


@pytest.mark.parametrize(
    "body,code",
    [
        ({"status": "incomplete"}, "INCOMPLETE"),
        ({"status": "completed", "output": []}, "INVALID_RESPONSE"),
        (
            {
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "refusal", "refusal": "raw sensitive text"},
                        ],
                    }
                ],
            },
            "REFUSED",
        ),
    ],
)
def test_incomplete_refusal_and_empty_are_not_memos(body: object, code: str) -> None:
    provider = OpenAIResponsesProvider("configured-model", SecretStr("fixture-credential"))
    with transport(body), pytest.raises(AgentProviderError, match=code) as failure:
        provider.generate_structured(request())
    assert "raw sensitive" not in str(failure.value)


def test_timeout_cannot_overlap_transport_via_a_new_runner(
    repository: AgentRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenAIResponsesProvider("configured-model", SecretStr("fixture-credential"))
    release = threading.Event()
    finished = threading.Event()
    calls = []

    class Output(BaseModel):
        answer: str

    def delayed(req: StructuredRequest) -> str:
        calls.append(req.run_id)
        release.wait(2)
        finished.set()
        return '{"answer":"fixture"}'

    monkeypatch.setattr(provider, "_generate", delayed)
    short = StructuredRequest(
        run_id="bounded",
        sections=request().sections,
        schema_json=request().schema_json,
        timeout_seconds=0.03,
    )
    try:
        with pytest.raises(AgentProviderError, match="TIMEOUT"):
            ProviderRunner(provider, repository).generate(short, Output)
        with pytest.raises(AgentProviderError, match="PROVIDER_FAILED"):
            ProviderRunner(provider, repository).generate(request(), Output)
        assert len(calls) == 1
    finally:
        release.set()
        assert finished.wait(2)
