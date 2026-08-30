# ADR-028 — Research orchestration (control plane)

## Context
Prompt 14 asks QUANT LAB to answer: what hypothesis was tested, using exactly what information, under what PIT constraints, with what models and alternatives, how many experiments were attempted, what was discovered, what failed, and whether the result survives validation and multiple-testing controls.

Prompts 01–13 already own the PIT fabric, feature/alpha/portfolio/risk/regime/adaptive/learning/ensemble engines, execution-research overlay, next-bar backtester, Prompt 05 validation suite and gate, integrity engine, and JSONL ledger. A second fabric, backtester, gate, or ledger would fork scientific identity.

## Problem
Uncoordinated engine calls hide search, omit losers, and let Sharpe fishing look like a pre-registered test.

## Options
1. Replace `quantlab.research` with a new mega-engine
2. Add `quantlab.orchestration` as a control plane that freezes hypotheses, records every candidate, and calls existing engines
3. Let the desktop run grids directly

## Decision
Option 2.

1. Control plane only. Existing engines remain authoritative.
2. Prompt 05 remains the only promotion gate. Synthetic cannot become `RESEARCH_CANDIDATE`.
3. Reuse `quantlab.research.multiple_testing` (BH / Bonferroni / Holm). No second FDR engine.
4. No hidden search. Every generated candidate is recorded. Dropping a loser is `hidden_candidate` FAIL.
5. No second ledger. Orchestration metadata extends `ExperimentRun` with defaults. `selection_stage="orchestration"`.
6. `HypothesisSpec` is distinct from `domain.research.ResearchHypothesis` so Prompt 01–13 constructors stay intact.
7. Pre-registered selection. Max-Sharpe-after-search is prohibited.
8. Falsification (sign reversal, cost stress) and ablation are first-class. A failed hypothesis is a valid result.
9. Dataset snapshot is pinned. Same spec + same snapshot = same identity. A new snapshot is a new lineage.
10. `LIVE_TRADING` remains false. Orchestration does not import brokers or call the OMS live path.
11. Desktop Research Control is a query viewer of `quantlab.app`.

## Consequences
- `quantlab hypothesis` / `quantlab experiment` are control-plane CLIs.
- `quantlab research discover|replicate|falsify|…` sit beside existing `research compare|gate|feature|execution` commands.
- Integrity gains orchestration flags; unimplemented remain `NOT_TESTED`.

## References
Prompt 14; ADR-011, ADR-015, ADR-019, ADR-027
