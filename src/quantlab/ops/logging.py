"""Ops logging helpers. Secrets are redacted. Does not shadow stdlib logging."""

from __future__ import annotations

from logging import getLogger

from quantlab.ops.secrets import redact

LOG = getLogger("quantlab.ops")


def info(message: str, *, secrets: tuple[str, ...] = ()) -> str:
    text = redact(message, secrets)
    LOG.info(text)
    return text
