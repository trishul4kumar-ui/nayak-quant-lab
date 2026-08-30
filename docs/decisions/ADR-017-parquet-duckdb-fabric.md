# ADR-017 — Parquet + DuckDB for the point-in-time fabric

## Context
Prompt 04 requires a research-grade historical information system, not a folder of CSVs. Options were a SQL warehouse (Postgres), a pure pandas/HDF5 store, or columnar files with an embeddable query engine.

## Problem
Every backtest must reconstruct **what was knowable at time T**. That needs versioned, checksummed, queryable storage that the desktop and CLI can run locally without a server.

## Options
1. Postgres as the canonical store (QuantDinger-style)
2. Per-instrument tiny Parquet files + pandas
3. **Year-partitioned Parquet + DuckDB queries + SQLite dataset catalog**

## Decision
**Option 3.**

- Raw artifacts are immutable bytes plus a SHA-256 sidecar.
- Validated bars are written as **year-partitioned Parquet**.
- Point-in-time queries run through **DuckDB** (`available_time <= as_of`).
- The dataset registry lives in **SQLite** (`metadata/catalog.sqlite`). A file on disk is not `RESEARCH_READY`.

Postgres is deferred until a licensed real dump and multi-user ops exist. Per-instrument files explode inode count and make as-of scans worse.

## Consequences
- `pyarrow` and `duckdb` are first-class dependencies.
- Strategies still consume `OHLCVBar` / `MarketState`; they never import DuckDB.
- Synthetic fixtures and user CSVs share the same ingest path.
- Official NSE holiday calendars and real prices are **not** bundled.

## References
Prompt 04; ADR-004; `docs/data/POINT_IN_TIME.md`
