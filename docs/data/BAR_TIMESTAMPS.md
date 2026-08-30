# Bar timestamps

| Field | Meaning |
|---|---|
| `event_time` | When the session/print occurred |
| `effective_time` | When the fact is economically effective |
| `available_time` | When a strategy could have known it (the backtest clock) |
| `ingestion_time` | When QUANT LAB stored the bytes |

All four are timezone-aware. Storage is UTC. Session date is `Asia/Kolkata`.

If a CSV supplies only a calendar date, `available_time` is set to that session's close **15:30 IST**. The dataset records `availability_convention=session_close`. This is a documented convention, not an invented reporting lag.

Naive datetimes (`2024-01-02 15:30:00` with no offset) are rejected.
