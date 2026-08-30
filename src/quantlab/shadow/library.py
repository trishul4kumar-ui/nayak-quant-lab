"""Seed shadow cycle inputs. Synthetic research snapshot — not NSE quotes."""

from __future__ import annotations

from quantlab.paper_oms.library import (
    SEED_ACCOUNT_ID,
    seed_account,
    seed_decision,
    seed_snapshot,
    seed_target,
)
from quantlab.paper_oms.models import PaperAccount
from quantlab.shadow.config import make_config
from quantlab.shadow.enums import ShadowMode
from quantlab.shadow.models import ShadowRequest

SEED_SHADOW_ACCOUNT = "SHADOW-001"


def seed_shadow_account() -> PaperAccount:
    return seed_account().model_copy(
        update={
            "account_id": SEED_SHADOW_ACCOUNT,
            "note": "Shadow paper books. Not a live broker balance. Not PAPER-001.",
        }
    )


def seed_request(*, mode: ShadowMode = ShadowMode.RESEARCH_PAPER) -> ShadowRequest:
    return ShadowRequest(mode=mode, data_kind="synthetic")


def seed_config(*, mode: ShadowMode = ShadowMode.RESEARCH_PAPER) -> object:
    return make_config(mode=mode)


__all__ = [
    "SEED_ACCOUNT_ID",
    "SEED_SHADOW_ACCOUNT",
    "seed_account",
    "seed_config",
    "seed_decision",
    "seed_request",
    "seed_shadow_account",
    "seed_snapshot",
    "seed_target",
]
