"""Econometric enumerations. Granger is predictive, never proof of causation."""

from enum import StrEnum


class EstimatorKind(StrEnum):
    OLS = "ols"
    HAC = "hac"
    CLUSTERED = "clustered"
    FAMA_MACBETH = "fama_macbeth"
    VAR = "var"
    VECM = "vecm"
    ENGLE_GRANGER = "engle_granger"
    JOHANSEN = "johansen"
    DID = "did"
    EVENT_STUDY = "event_study"
    SYNTHETIC_CONTROL = "synthetic_control"
    UNAVAILABLE = "unavailable"


class CausalClaim(StrEnum):
    NONE = "none"
    PREDICTIVE = "predictive"
    ASSOCIATIONAL = "associational"
    CAUSAL_UNDER_ASSUMPTIONS = "causal_under_assumptions"


class BreakKind(StrEnum):
    CUSUM = "cusum"
    ROLLING = "rolling"
    KNOWN_DATE = "known_date"
    UNKNOWN = "unknown"


class PanelEffect(StrEnum):
    POOLED = "pooled"
    ENTITY = "entity"
    TIME = "time"
    TWO_WAY = "two_way"
