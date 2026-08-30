"""Canonical instrument master. Tickers are labels, not identity."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import IST
from quantlab.data.fabric.types import DataKind
from quantlab.domain.models import Instrument


class CanonicalInstrument(BaseModel):
    security_id: str
    exchange: str
    segment: str = "CM"
    symbol: str
    isin: str = ""
    security_type: str = "equity"
    series: str = "EQ"
    currency: str = "INR"
    tick_size: float = 0.05
    lot_size: int = 1
    listing_date: datetime | None = None
    delisting_date: datetime | None = None
    status: str = "listed"
    data_kind: DataKind = DataKind.SYNTHETIC

    def instrument_id(self) -> InstrumentId:
        return InstrumentId(exchange=self.exchange, symbol=self.symbol)

    def is_listed_at(self, as_of: datetime) -> bool:
        instant = as_of.astimezone(IST)
        if self.listing_date is not None and instant < self.listing_date.astimezone(IST):
            return False
        return not (
            self.delisting_date is not None and instant >= self.delisting_date.astimezone(IST)
        )

    def to_domain(self, as_of: datetime | None = None) -> Instrument:
        listed = True if as_of is None else self.is_listed_at(as_of)
        return Instrument(
            id=self.instrument_id(),
            lot_size=self.lot_size,
            tick_size=self.tick_size,
            currency=self.currency,
            listed=listed,
            name=self.symbol,
            listing_date=None if self.listing_date is None else self.listing_date.isoformat(),
            delisting_date=None if self.delisting_date is None else self.delisting_date.isoformat(),
            isin=self.isin,
            security_id=self.security_id,
        )


class SymbolBinding(BaseModel):
    security_id: str
    symbol: str
    valid_from: datetime
    valid_to: datetime | None = None


class InstrumentMaster:
    def __init__(self) -> None:
        self._by_id: dict[str, CanonicalInstrument] = {}
        self._bindings: list[SymbolBinding] = []

    def add(self, instrument: CanonicalInstrument) -> None:
        self._by_id[instrument.security_id] = instrument

    def add_symbol(self, binding: SymbolBinding) -> None:
        self._bindings.append(binding)

    def get(self, security_id: str) -> CanonicalInstrument | None:
        return self._by_id.get(security_id)

    def resolve_symbol(self, symbol: str, as_of: datetime) -> CanonicalInstrument | None:
        needle = symbol.strip().upper()
        for binding in self._bindings:
            if binding.symbol.upper() != needle:
                continue
            if as_of < binding.valid_from:
                continue
            if binding.valid_to is not None and as_of >= binding.valid_to:
                continue
            return self._by_id.get(binding.security_id)
        for inst in self._by_id.values():
            if inst.symbol.upper() == needle and inst.is_listed_at(as_of):
                return inst
        return None

    def all(self) -> list[CanonicalInstrument]:
        return list(self._by_id.values())

    def symbol_at(self, security_id: str, as_of: datetime) -> str | None:
        """Historical label valid at T. Never maps today's ticker backward by name."""
        matches = [
            binding
            for binding in self._bindings
            if binding.security_id == security_id
            and as_of >= binding.valid_from
            and (binding.valid_to is None or as_of < binding.valid_to)
        ]
        if matches:
            matches.sort(key=lambda row: row.valid_from, reverse=True)
            return matches[0].symbol
        inst = self._by_id.get(security_id)
        if inst is None:
            return None
        if inst.is_listed_at(as_of):
            return inst.symbol
        return None
