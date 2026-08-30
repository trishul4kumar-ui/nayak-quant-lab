"""Stable identifiers. Tickers are not identities."""

from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class InstrumentId(BaseModel):
    """Exchange-scoped instrument identity."""

    model_config = {"frozen": True}

    exchange: str
    symbol: str
    asset_class: str = "equity"

    @field_validator("exchange", "symbol", "asset_class")
    @classmethod
    def _normalize(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("identifier parts cannot be empty")
        return cleaned.upper()

    def __str__(self) -> str:
        return f"{self.exchange}:{self.symbol}"

    @classmethod
    def parse(cls, raw: str) -> InstrumentId:
        exchange, _, symbol = raw.partition(":")
        if not symbol:
            raise ValueError(f"expected EXCHANGE:SYMBOL, got {raw!r}")
        return cls(exchange=exchange, symbol=symbol)


class OrderId(BaseModel):
    model_config = {"frozen": True}

    value: str = Field(default_factory=lambda: uuid4().hex)

    def __str__(self) -> str:
        return self.value


class ExperimentId(BaseModel):
    model_config = {"frozen": True}

    value: str = Field(default_factory=lambda: uuid4().hex)

    def __str__(self) -> str:
        return self.value


class HypothesisId(BaseModel):
    model_config = {"frozen": True}

    value: str = Field(default_factory=lambda: uuid4().hex)

    def __str__(self) -> str:
        return self.value


class AlphaId(BaseModel):
    model_config = {"frozen": True}

    value: str = Field(default_factory=lambda: uuid4().hex)

    def __str__(self) -> str:
        return self.value
