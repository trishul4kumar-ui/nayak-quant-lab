# ADR-034 — Production Market Data, Corporate Actions & Data Quality

## Context
Prompt 20 upgrades the existing PIT fabric into a production-grade Indian-market data foundation without inventing market history.

## Decision
Extend `quantlab.data` (do not create a second data package). Raw bytes are immutable and checksummed. Tickers are labels. `universe.as_of(T)` is historical. Corporate-action timing that is unknown is `NOT_TESTED`. Official NSE holidays are not fabricated. Downstream research uses `market_data.get(..., as_of=...)` with `available_time <= as_of`.

## Consequences
- Changing source bytes creates a new version
- Snapshots bind dataset, master, calendar, CA, and universe versions
- Cross-source disagreements are recorded, not auto-resolved toward the favorable value
