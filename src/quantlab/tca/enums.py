"""TCA enumerations. Modelled is never labelled observed."""

from enum import StrEnum


class TCAKind(StrEnum):
    OBSERVED = "observed_tca"
    MODELLED = "modelled_tca"
    CALIBRATED = "calibrated_tca"
    STRESSED = "stressed_tca"


class ArrivalPolicy(StrEnum):
    DECISION_PRICE = "decision_price"
    ARRIVAL_SNAPSHOT = "arrival_snapshot"
    USER_SUPPLIED = "user_supplied"
    BAR_DERIVED = "bar_derived"
    UNAVAILABLE = "unavailable"


class FragilityStatus(StrEnum):
    ROBUST = "robust"
    FRAGILE = "fragile"
    ECONOMICALLY_UNVIABLE = "economically_unviable"
    NOT_TESTED = "not_tested"


class CapacityStatus(StrEnum):
    FEASIBLE = "feasible"
    BREACH = "breach"
    NOT_TESTED = "not_tested"


class SpreadKind(StrEnum):
    QUOTED = "quoted"
    EFFECTIVE = "effective"
    REALIZED = "realized"
    BAR_PROXY = "bar_proxy"
    UNAVAILABLE = "unavailable"
