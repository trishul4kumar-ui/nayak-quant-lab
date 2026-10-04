"""Canonical identities shared by all desk artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, model_validator

_SECRET = re.compile(
    r"(?:Bearer\s+\S+|sk-[A-Za-z0-9_-]{12,}|"
    r"(?:api[_ -]?key|access[_ -]?token|api[_ -]?secret|password)\s*[:=]\s*\S+)",
    re.IGNORECASE,
)
_SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "api_secret",
        "access_token",
        "client_secret",
        "password",
        "authorization",
    }
)


def reject_sensitive_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in _SENSITIVE_KEYS:
                raise ValueError("secret-bearing field is forbidden in research artifacts")
            reject_sensitive_payload(item)
    elif isinstance(value, list | tuple):
        for item in value:
            reject_sensitive_payload(item)
    elif isinstance(value, str) and value.lstrip().startswith(("{", "[")):
        try:
            parsed = json.loads(value)
        except (ValueError, TypeError):
            return
        reject_sensitive_payload(parsed)


def digest(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def safe_text(value: str) -> str:
    return _SECRET.sub("[REDACTED]", value)


class Artifact(BaseModel):
    """Tuple-only domain containers make frozen models deeply immutable.

    Hashes include the creation time supplied by the orchestrator. Loading an artifact
    validates its hash again, including after a restart. Never use model_construct/copy
    to install unvalidated provider output.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    schema_version: str = "agents-v1"
    created_at: AwareDatetime
    content_hash: str = ""

    @model_validator(mode="after")
    def seal(self) -> Self:
        payload = self.model_dump(mode="json", exclude={"content_hash"})
        reject_sensitive_payload(payload)
        canonical = json.dumps(payload, sort_keys=True)
        if safe_text(canonical) != canonical:
            raise ValueError("secret-like content is forbidden in research artifacts")
        expected = digest({"contract": type(self).__name__, "payload": payload})
        if self.content_hash and self.content_hash != expected:
            raise ValueError("artifact content hash mismatch")
        object.__setattr__(self, "content_hash", expected)
        return self

    def verified(self) -> Self:
        return type(self).model_validate(self.model_dump(mode="json"))

    def identity_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
