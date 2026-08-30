# ADR-009 — Experiment ledger

## Context
Qlib Recorders persist params, metrics, artifacts. TradingAgents writes a markdown decision log. Untracked notebooks are how leakage becomes folklore.

## Problem
The same momentum slice must be replayable.

## Options
1. MLflow from Day 1
2. JSONL ledger with git commit, dataset version, costs, metrics, integrity flags
3. Nothing until Postgres

## Decision
Option 2. File `experiments/ledger.jsonl`. Postgres later (QuantDinger) without changing the schema much.

## Consequences
- No extra daemon for Day 1
- Schema is versioned on the record itself

## References
Qlib `qlib/workflow/recorder.py`
