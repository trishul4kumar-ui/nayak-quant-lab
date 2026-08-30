"""Data-fabric enumerations. Strategies never import a vendor SDK."""

from __future__ import annotations

from enum import StrEnum


class DataKind(StrEnum):
    SYNTHETIC = "synthetic"
    REAL = "real"


class PriceKind(StrEnum):
    RAW_PRICE = "raw_price"
    ADJUSTED_PRICE = "adjusted_price"
    TOTAL_RETURN = "total_return"


class DatasetState(StrEnum):
    RAW = "raw"
    INGESTED = "ingested"
    NORMALIZED = "normalized"
    VALIDATED = "validated"
    CURATED = "curated"
    PIT_VALIDATED = "pit_validated"
    RESEARCH_READY = "research_ready"
    QUARANTINED = "quarantined"
    DEPRECATED = "deprecated"
    NOT_READY = "not_ready"


class FeatureStatus(StrEnum):
    READY = "ready"
    INSUFFICIENT_HISTORY = "insufficient_history"
    MISSING_DATA = "missing_data"
    INVALID = "invalid"


class CorporateActionType(StrEnum):
    DIVIDEND = "dividend"
    SPLIT = "split"
    BONUS = "bonus"
    RIGHTS = "rights"
    MERGER = "merger"
    DEMERGER = "demerger"
    SPIN_OFF = "spin_off"
    SYMBOL_CHANGE = "symbol_change"
    FACE_VALUE_CHANGE = "face_value_change"
    DELISTING = "delisting"
    RELISTING = "relisting"


class DividendPolicy(StrEnum):
    PRICE_RETURN = "price_return"
    TOTAL_RETURN = "total_return"
    CASH_DIVIDEND = "cash_dividend"
