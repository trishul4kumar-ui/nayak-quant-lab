"""Provider-neutral JSON interface and bounded, audited schema validation."""

from __future__ import annotations

import json
import os
import queue
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ConfigDict, SecretStr, ValidationError

from quantlab.agents.contracts import AgentModelIdentity
from quantlab.agents.errors import AgentProviderError
from quantlab.agents.hashing import digest
from quantlab.agents.repository import AgentRepository

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class StructuredRequest:
    run_id: str
    sections: tuple[tuple[str, str], ...]
    schema_json: str
    timeout_seconds: float = 30.0
    max_output_tokens: int = 2000

    def prompt_hash(self) -> str:
        return digest({"sections": self.sections, "schema": self.schema_json})


class ProviderHealth(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    provider: str
    model: str
    configured: bool
    observed_status: str


class AgentModelProvider(Protocol):
    def generate_structured(self, request: StructuredRequest) -> str: ...
    def continue_structured(self, request: StructuredRequest) -> str: ...
    def health(self) -> ProviderHealth: ...
    def identity(self) -> AgentModelIdentity: ...


class UnavailableProvider:
    def generate_structured(self, request: StructuredRequest) -> str:
        raise AgentProviderError("PROVIDER_NOT_CONFIGURED")

    def continue_structured(self, request: StructuredRequest) -> str:
        return self.generate_structured(request)

    def health(self) -> ProviderHealth:
        return ProviderHealth(
            provider="unconfigured", model="none", configured=False, observed_status="UNAVAILABLE"
        )

    def identity(self) -> AgentModelIdentity:
        return AgentModelIdentity(
            created_at=datetime(2026, 10, 4, tzinfo=UTC),
            provider="unconfigured",
            model="none",
            version="39-v1",
        )


def strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Responses requires all object fields required and additionalProperties=false."""
    result: dict[str, Any] = {}
    for key, value in schema.items():
        if key == "default":
            continue
        if isinstance(value, dict):
            result[key] = strict_schema(value)
        elif isinstance(value, list):
            result[key] = [strict_schema(row) if isinstance(row, dict) else row for row in value]
        else:
            result[key] = value
    if result.get("type") == "object":
        result["additionalProperties"] = False
        result["required"] = list(result.get("properties", {}))
    return result


class OpenAIResponsesProvider:
    """Credentials used only at transport; fixed destination prevents endpoint exfiltration."""

    def __init__(self, model: str, api_key: SecretStr) -> None:
        self._model = model
        self._api_key = api_key
        self._identity = AgentModelIdentity(
            created_at=datetime(2026, 10, 4, tzinfo=UTC),
            provider="openai-responses",
            model=model,
            version="responses-json-schema-v1",
        )
        self._observed_status = "NOT_TESTED"

    def identity(self) -> AgentModelIdentity:
        return self._identity

    def health(self) -> ProviderHealth:
        return ProviderHealth(
            provider=self._identity.provider,
            model=self._model,
            configured=bool(self._api_key.get_secret_value() and self._model),
            observed_status=self._observed_status,
        )

    def generate_structured(self, request: StructuredRequest) -> str:
        payload = {
            "model": self._model,
            "store": False,
            "input": [
                {"role": "system", "content": request.sections[0][1]},
                {"role": "user", "content": json.dumps(dict(request.sections[1:]))},
            ],
            "max_output_tokens": request.max_output_tokens,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "quant_desk_result",
                    "strict": True,
                    "schema": strict_schema(json.loads(request.schema_json)),
                }
            },
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self._api_key.get_secret_value(),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=request.timeout_seconds) as response:
                raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise AgentProviderError("PROVIDER_RESPONSE_TOO_LARGE")
            body = json.loads(raw)
            if body.get("status") != "completed":
                raise AgentProviderError("PROVIDER_INCOMPLETE")
            text_parts: list[str] = []
            for output in body.get("output", []):
                if output.get("type") != "message":
                    continue
                for part in output.get("content", []):
                    if part.get("type") == "refusal":
                        raise AgentProviderError("PROVIDER_REFUSED")
                    if part.get("type") == "output_text":
                        text_parts.append(str(part["text"]))
            if len(text_parts) != 1:
                raise AgentProviderError("PROVIDER_INVALID_RESPONSE")
            self._observed_status = "RESPONDED"
            return text_parts[0]
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError, TypeError):
            self._observed_status = "UNAVAILABLE"
            raise AgentProviderError("PROVIDER_TRANSPORT_OR_RESPONSE_FAILED") from None

    def continue_structured(self, request: StructuredRequest) -> str:
        # Stateless continuation resends the bounded frozen evidence; no hidden vendor memory.
        return self.generate_structured(request)


def configured_provider() -> AgentModelProvider:
    key, model = os.environ.get("OPENAI_API_KEY"), os.environ.get("QUANT_LAB_AGENT_MODEL")
    if not key or not model:
        return UnavailableProvider()
    return OpenAIResponsesProvider(model, SecretStr(key))


class ProviderRunner:
    def __init__(self, provider: AgentModelProvider, repository: AgentRepository) -> None:
        self.provider, self.repository = provider, repository
        self._slot = threading.BoundedSemaphore(1)

    def generate(
        self,
        request: StructuredRequest,
        contract: type[T],
        *,
        cancel: threading.Event | None = None,
        schema_retries: int = 1,
    ) -> T:
        if not 0 <= schema_retries <= 2 or not 0 < request.timeout_seconds <= 120:
            raise AgentProviderError("INVALID_PROVIDER_BUDGET")
        deadline = time.monotonic() + request.timeout_seconds
        for attempt in range(schema_retries + 1):
            if cancel is not None and cancel.is_set():
                raise AgentProviderError("PROVIDER_CANCELLED")
            self.repository.audit(
                "PROVIDER_REQUESTED",
                run_id=request.run_id,
                now=datetime.now(UTC),
                artifact_hash=request.prompt_hash(),
            )
            raw = self._call(request, deadline, cancel, continuing=attempt > 0)
            # Hash only; do not persist or log the raw provider text.
            self.repository.audit(
                "PROVIDER_RESPONSE",
                run_id=request.run_id,
                now=datetime.now(UTC),
                artifact_hash=digest(raw),
            )
            try:
                return contract.model_validate_json(raw)
            except ValidationError:
                self.repository.audit(
                    "SCHEMA_REJECTED",
                    run_id=request.run_id,
                    now=datetime.now(UTC),
                    safe_code="INVALID_STRUCTURED_OUTPUT",
                )
                if attempt == schema_retries:
                    raise AgentProviderError("INVALID_STRUCTURED_OUTPUT") from None
        raise AgentProviderError("INVALID_STRUCTURED_OUTPUT")

    def _call(
        self,
        request: StructuredRequest,
        deadline: float,
        cancel: threading.Event | None,
        *,
        continuing: bool,
    ) -> str:
        if not self._slot.acquire(blocking=False):
            raise AgentProviderError("PROVIDER_BUSY")
        result: queue.Queue[str | AgentProviderError] = queue.Queue(maxsize=1)

        def invoke() -> None:
            try:
                fn = (
                    self.provider.continue_structured
                    if continuing
                    else self.provider.generate_structured
                )
                result.put(fn(request))
            except Exception:
                result.put(AgentProviderError("PROVIDER_FAILED"))
            finally:
                self._slot.release()

        threading.Thread(target=invoke, daemon=True, name="quantlab-provider").start()
        while True:
            if cancel is not None and cancel.is_set():
                raise AgentProviderError("PROVIDER_CANCELLED")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AgentProviderError("PROVIDER_TIMEOUT")
            try:
                value = result.get(timeout=min(remaining, 0.05))
                if isinstance(value, AgentProviderError):
                    raise value
                return value
            except queue.Empty:
                continue
