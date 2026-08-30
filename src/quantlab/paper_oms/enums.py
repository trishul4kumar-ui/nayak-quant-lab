"""Paper OMS enumerations. Paper fills are not broker confirmations."""

from enum import StrEnum


class OrderAction(StrEnum):
    BUY = "buy"
    SELL = "sell"
    INCREASE = "increase"
    DECREASE = "decrease"
    EXIT = "exit"
    NO_ACTION = "no_action"
    ABSTAIN = "abstain"


class OrderLifecycleState(StrEnum):
    CREATED = "created"
    VALIDATED = "validated"
    PLANNED = "planned"
    SUBMITTED_PAPER = "submitted_paper"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    RECONCILED = "reconciled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    FAILED = "failed"


class EventType(StrEnum):
    ORDER_CREATED = "OrderCreated"
    ORDER_VALIDATED = "OrderValidated"
    ORDER_PLANNED = "OrderPlanned"
    ORDER_SUBMITTED_PAPER = "OrderSubmittedPaper"
    PAPER_FILL_RECEIVED = "PaperFillReceived"
    ORDER_PARTIALLY_FILLED = "OrderPartiallyFilled"
    ORDER_FILLED = "OrderFilled"
    ORDER_CANCELLED = "OrderCancelled"
    ORDER_REJECTED = "OrderRejected"
    ORDER_EXPIRED = "OrderExpired"
    ORDER_RECONCILED = "OrderReconciled"
    ACCOUNT_RESET = "AccountReset"


class ReconciliationStatus(StrEnum):
    RECONCILED = "reconciled"
    RECONCILIATION_BREAK = "reconciliation_break"
    NOT_TESTED = "not_tested"


class RoundingPolicy(StrEnum):
    FLOOR_LOT = "floor_lot"


class PaperOrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"


class TimeInForce(StrEnum):
    DAY = "day"
    IOC = "ioc"


class FillPolicy(StrEnum):
    SIMULATED = "simulated"
    PARTICIPATION_CAPPED = "participation_capped"
    RATIO_CAPPED = "ratio_capped"
    FULL = "full"


class LiquidityMark(StrEnum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    INSUFFICIENT = "insufficient"
    UNFILLED = "unfilled"
    NOT_TESTED = "not_tested"


class OMSRunStatus(StrEnum):
    CREATED = "created"
    PLANNED = "planned"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    REJECTED = "rejected"
    ABSTAINED = "abstained"
    FAILED = "failed"


class RemainderFate(StrEnum):
    OPEN = "open"
    CANCELLED_REMAINDER = "cancelled_remainder"
    EXPIRED_REMAINDER = "expired_remainder"
    FILLED = "filled"


TERMINAL_STATES: frozenset[OrderLifecycleState] = frozenset(
    {
        OrderLifecycleState.REJECTED,
        OrderLifecycleState.CANCELLED,
        OrderLifecycleState.EXPIRED,
        OrderLifecycleState.FAILED,
        OrderLifecycleState.RECONCILED,
    }
)

ALLOWED_TRANSITIONS: dict[OrderLifecycleState, frozenset[OrderLifecycleState]] = {
    OrderLifecycleState.CREATED: frozenset(
        {
            OrderLifecycleState.VALIDATED,
            OrderLifecycleState.REJECTED,
            OrderLifecycleState.CANCELLED,
            OrderLifecycleState.FAILED,
        }
    ),
    OrderLifecycleState.VALIDATED: frozenset(
        {
            OrderLifecycleState.PLANNED,
            OrderLifecycleState.REJECTED,
            OrderLifecycleState.CANCELLED,
            OrderLifecycleState.FAILED,
        }
    ),
    OrderLifecycleState.PLANNED: frozenset(
        {
            OrderLifecycleState.SUBMITTED_PAPER,
            OrderLifecycleState.REJECTED,
            OrderLifecycleState.CANCELLED,
            OrderLifecycleState.FAILED,
        }
    ),
    OrderLifecycleState.SUBMITTED_PAPER: frozenset(
        {
            OrderLifecycleState.ACKNOWLEDGED,
            OrderLifecycleState.REJECTED,
            OrderLifecycleState.CANCELLED,
            OrderLifecycleState.EXPIRED,
            OrderLifecycleState.FAILED,
        }
    ),
    OrderLifecycleState.ACKNOWLEDGED: frozenset(
        {
            OrderLifecycleState.PARTIALLY_FILLED,
            OrderLifecycleState.FILLED,
            OrderLifecycleState.CANCELLED,
            OrderLifecycleState.EXPIRED,
            OrderLifecycleState.FAILED,
        }
    ),
    OrderLifecycleState.PARTIALLY_FILLED: frozenset(
        {
            OrderLifecycleState.PARTIALLY_FILLED,
            OrderLifecycleState.FILLED,
            OrderLifecycleState.CANCELLED,
            OrderLifecycleState.EXPIRED,
            OrderLifecycleState.FAILED,
            OrderLifecycleState.RECONCILED,
        }
    ),
    OrderLifecycleState.FILLED: frozenset({OrderLifecycleState.RECONCILED}),
    OrderLifecycleState.RECONCILED: frozenset(),
    OrderLifecycleState.REJECTED: frozenset(),
    OrderLifecycleState.CANCELLED: frozenset(),
    OrderLifecycleState.EXPIRED: frozenset(),
    OrderLifecycleState.FAILED: frozenset(),
}
