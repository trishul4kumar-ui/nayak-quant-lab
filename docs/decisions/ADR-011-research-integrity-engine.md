# ADR-011 — Research integrity engine

## Context
Prompt 02 requires PASS/WARN/FAIL/NOT_TESTED per check. Boolean flags from Prompt 01 were insufficient.

## Problem
A profitable backtest must not look “clean” if leakage or zero costs were used.

## Options
1. Keep booleans
2. Dedicated IntegrityReport produced by every experiment
3. LLM critic as the integrity authority

## Decision
Option 2. Deterministic checks. AI may only *read* the report.

## Consequences
- Zero transaction costs → WARN or FAIL
- Same-bar fill → FAIL look-ahead
- Unimplemented checks are NOT_TESTED, never silent PASS
