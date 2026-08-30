# ADR-002 — Data provider abstraction

## Context
OpenBB isolates providers from consumers. Qlib uses a URI-based data provider. Vendor SDKs (Kite, Yahoo, AKShare) must not leak.

## Problem
How does research request bars without knowing the vendor?

## Options
1. Direct Kite/OpenAlgo calls in notebooks
2. Protocol `MarketDataProvider` + adapters (memory, CSV, later OpenAlgo)
3. Embed OpenBB as a dependency (AGPL)

## Decision
Option 2. `quantlab.data.contracts.MarketDataProvider`. Day 1 adapter: in-memory synthetic NSE-like bars.

## Consequences
- Research depends only on `InstrumentId` and `OHLCVBar`
- Adding NSE dumps is an adapter, not a rewrite

## References
OpenBB `openbb_platform/providers`; Qlib `qlib/data`
