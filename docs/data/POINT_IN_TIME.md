# Point-in-time data

See ADR-004 and ADR-017.

Every bar carries `event_time`, `effective_time`, `available_time`, and `ingestion_time`. Naive datetimes are rejected.

The research question is:

> What information was actually available to the strategy at time T?

The fabric answers that with:

```text
available_time <= as_of
```

Walk-forward and the research gate consume the same PIT query. A later `available_time` cannot leak into an earlier train window.

DuckDB queries on year-partitioned Parquet enforce the filter. The Python store raises `LookAheadError` if a row still leaks. MarketState and the next-bar backtester use `PointInTime.is_available_at`, not `event_time <= as_of`.

Delayed vendor prints of a past session stay in storage but are invisible at earlier decision times.

`NOT_TESTED` never becomes `PASS`. Missing corporate-action or universe-membership history is recorded as `NOT_TESTED`.

Synthetic bars (`data_kind=synthetic`) are architecture fixtures. They are never live-grade NSE history.
