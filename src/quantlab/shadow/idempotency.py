"""Idempotent cycle lookup. Same key returns the prior result, not a second stream."""

from __future__ import annotations

from quantlab.shadow.models import ShadowResult
from quantlab.shadow.state import lookup as lookup_key
from quantlab.shadow.state import put_result


def lookup(key: str) -> ShadowResult | None:
    return lookup_key(key)


def remember(key: str, result: ShadowResult) -> ShadowResult:
    return put_result(result, key=key)
