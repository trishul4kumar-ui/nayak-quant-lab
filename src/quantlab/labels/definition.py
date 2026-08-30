"""Forward labels. Never used as feature inputs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class LabelKind(StrEnum):
    FORWARD_RETURN = "forward_return"
    FORWARD_EXCESS_RETURN = "forward_excess_return"
    FORWARD_VOLATILITY = "forward_volatility"
    FORWARD_DRAWDOWN = "forward_drawdown"
    FORWARD_BINARY_DIRECTION = "forward_binary_direction"


class LabelDefinition(BaseModel):
    label_id: str
    version: str
    kind: LabelKind
    horizon: int
    mathematical_definition: str
    price_field: str = "close"
    benchmark: str | None = None
    implementation_version: str = "0.6.0"
    notes: str = ""


def forward_return(horizon: int) -> LabelDefinition:
    return LabelDefinition(
        label_id=f"forward_return_{horizon}",
        version="1",
        kind=LabelKind.FORWARD_RETURN,
        horizon=horizon,
        mathematical_definition=f"P(T+{horizon})/P(T)-1; known at T+{horizon}",
    )


def forward_excess_return(horizon: int, benchmark: str | None = None) -> LabelDefinition:
    return LabelDefinition(
        label_id=f"forward_excess_return_{horizon}",
        version="1",
        kind=LabelKind.FORWARD_EXCESS_RETURN,
        horizon=horizon,
        benchmark=benchmark,
        mathematical_definition=(
            f"r(T,{horizon}) - r_benchmark; NOT_TESTED without a PIT benchmark series"
        ),
        notes="cash/unavailable benchmark → NOT_TESTED; NIFTY is not invented",
    )


def forward_volatility(horizon: int) -> LabelDefinition:
    return LabelDefinition(
        label_id=f"forward_volatility_{horizon}",
        version="1",
        kind=LabelKind.FORWARD_VOLATILITY,
        horizon=horizon,
        mathematical_definition=f"std of simple returns from T to T+{horizon}",
    )


def forward_drawdown(horizon: int) -> LabelDefinition:
    return LabelDefinition(
        label_id=f"forward_drawdown_{horizon}",
        version="1",
        kind=LabelKind.FORWARD_DRAWDOWN,
        horizon=horizon,
        mathematical_definition=f"max_drawdown of close path from T to T+{horizon}",
    )


def forward_binary_direction(horizon: int) -> LabelDefinition:
    return LabelDefinition(
        label_id=f"forward_binary_direction_{horizon}",
        version="1",
        kind=LabelKind.FORWARD_BINARY_DIRECTION,
        horizon=horizon,
        mathematical_definition=f"1 if P(T+{horizon})/P(T)-1 > 0 else 0",
    )
