# ADR-029 — Alpha discovery (symbolic / genetic research layer)

## Context
Prompt 15 asks QUANT LAB to answer: can the lab systematically discover novel mathematical relationships between PIT-available information at decision time T and future market behavior, while controlling expression complexity, data mining, redundancy, multiple testing, temporal leakage, and researcher degrees of freedom?

Prompts 01–14 already own the PIT fabric, feature/label/alpha engines, portfolio/risk/regime/adaptive/learning/ensemble/execution-research layers, Prompt 14 control plane, Prompt 05 gate, integrity engine, and JSONL ledger. A second fabric, backtester, FDR engine, gate, or ledger would fork scientific identity.

`domain.research.SignalGenome` / `ExpressionNode` remain the Prompt 02 genome. Prompt 15 adds a typed discovery AST (`quantlab.discovery.expression.ExprNode`) and does not put genetic search into `quantlab.research.genome`.

## Problem
Unrestricted expression search can manufacture in-sample Sharpe, hide losers, leak labels into generators, and treat a discovered tree as a live alpha.

## Options
1. Replace the feature/alpha engines with a genetic programming runtime
2. Add `quantlab.discovery` as a research layer that generates, records, and falsifies expressions, then hands survivors to Prompt 14 / Prompt 05
3. Run genetic search in the desktop Qt thread

## Decision
Option 2.

1. Discovery layer only. It generates research hypotheses. It does not create orders, place trades, or promote.
2. Prompt 05 remains the only promotion gate. Synthetic cannot become `RESEARCH_CANDIDATE`.
3. Reuse `quantlab.orchestration.multiple_testing.family_correction` → `quantlab.research.multiple_testing`. No second FDR engine.
4. No hidden search. Every generated candidate is recorded. Dropping a loser is `hidden_candidate` FAIL.
5. No second ledger. Discovery metadata extends `ExperimentRun` with defaults. `selection_stage="discovery"`.
6. Typed serializable AST. Invalid compositions raise `DiscoveryError`. Labels are not generator primitives (`label_as_feature`).
7. Frozen search budget. Extending generations after seeing results is `posthoc_search_budget` FAIL. Holdout is not used for selection.
8. Fitness is multi-objective (train IC, complexity, redundancy, turnover, coverage). Not Sharpe-max.
9. `quantlab research discover` remains Prompt 14. Prompt 15 uses `quantlab discovery …` and non-colliding research aliases (`symbolic`, `genetic`, `alpha-discovery`).
10. `LIVE_TRADING` remains false. Discovery does not import brokers or call the OMS live path.
11. Desktop Discovery Lab is a query viewer of `quantlab.app`.
12. Genetic search does not replace the Prompt 06 feature engine. Allowed seeds reference existing features.

## Consequences
- A spectacular in-sample expression that fails OOS is a successful falsification, not a successful alpha.
- `DISCOVERY ≠ CONFIRMATION ≠ VALIDATION ≠ REPLICATION ≠ PROMOTION`
- Integrity gains discovery flags; unimplemented remain `NOT_TESTED`.

## References
Prompt 15; ADR-011, ADR-015, ADR-019, ADR-027, ADR-028
