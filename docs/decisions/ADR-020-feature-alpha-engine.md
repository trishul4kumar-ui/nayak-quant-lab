# ADR-020 — Feature & alpha research engine

## Context
Prompt 06 asks whether a PIT-valid relationship exists between information at T and later behavior. The lab already has MarketState features, a genome AST, cross-sectional IC, a PIT fabric, and Prompt 05 validation. A second data fabric or second backtester would fork semantics.

## Problem
Stuffing feature identity, labels, and IC experiments into `quantlab.research` would recreate the circular import that already forced `research/__init__.py` to stay thin (`suite` → `engine` → `portfolio` → `strategy` → `research`).

## Options
1. Expand `research/` with feature/label modules imported from `__init__`
2. New packages `features`, `labels`, `alpha` with a one-way dependency toward research/backtest
3. Unrestricted Python expressions and a large indicator zoo

## Decision
Option 2.

- `FeatureDefinition` is hashed identity; formula change → new version; no overwrite
- Labels are a separate package and never enter the feature engine
- Genome AST gains `add` / `sub` / `scale`; no `eval`
- Cache keys include snapshot, feature identity, universe, range, frequency, normalization
- Alpha experiments call Prompt 05’s gate; they do not replace it
- Fabric `FeatureStatus` stays compute-readiness; research uses `FeatureLifecycle`
- `domain.research.Feature` remains a value at a timestamp

## Consequences
- `momentum_20` stays numerically identical to MarketState
- Synthetic known-signal tests prove machinery; they are not NSE evidence
- Rolling beta, sector, cap, ADV, and excess-vs-index stay `NOT_TESTED` until PIT data exists
- Desktop Features / Alpha Lab are query viewers

## References
Prompt 06; ADR-004; ADR-010; ADR-012; ADR-019
