# Order lifecycle

**Status:** Prompt 18 / ADR-032  
**Version:** 1.8.0

Paper orders use a closed state machine:

```
CREATED → VALIDATED → PLANNED → SUBMITTED_PAPER → ACKNOWLEDGED
    → PARTIALLY_FILLED → FILLED → RECONCILED
```

Terminal states: `REJECTED`, `CANCELLED`, `EXPIRED`, `FAILED`, `RECONCILED`.

Invalid transitions raise `InvalidOrderTransition`. Status is not a free-form field.

Every transition emits an immutable `OrderEvent` (`event_id`, `sequence_number`, `previous_state`, `new_state`, `payload_hash`, causation/correlation ids).

`CANCELLED_REMAINDER` and `EXPIRED_REMAINDER` keep residual quantity visible. The engine never assumes `requested_quantity == filled_quantity`.
