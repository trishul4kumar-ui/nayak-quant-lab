from enum import StrEnum


class RiskState(StrEnum):
    NORMAL = "normal"
    CAUTION = "caution"
    RESTRICTED = "restricted"
    HALT = "halt"
    EMERGENCY = "emergency"


def allows_new_exposure(state: RiskState) -> bool:
    return state not in {RiskState.HALT, RiskState.EMERGENCY}
