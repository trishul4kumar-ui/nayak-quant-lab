from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import SecretStr

from quantlab.agents.errors import AgentProviderError
from quantlab.agents.provider import OpenAIResponsesProvider, StructuredRequest


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
