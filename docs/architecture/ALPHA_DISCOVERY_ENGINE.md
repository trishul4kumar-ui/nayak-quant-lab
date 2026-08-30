# Alpha Discovery Engine

**Status:** Prompt 15 / ADR-029  
**Version:** 1.5.0

Prompt 15 is a **research discovery layer**. It generates candidate mathematical expressions from PIT-available features, then falsifies, deduplicates, and records them. It is not an alpha factory, not a second backtester, and not a promotion gate.

```
PIT fabric → features / labels
    → quantlab.discovery (grammar, search, fitness, novelty)
    → Prompt 14 orchestration (family, lineage, multiple testing)
    → Prompt 05 gate
    → ledger (selection_stage=discovery)
```

A discovered expression is a **research hypothesis** until independently validated.

## Package

`quantlab.discovery` owns the typed AST (`ExprNode`), grammar, generator, mutation/crossover, PIT evaluator, multi-objective fitness, novelty/redundancy, falsification, frozen search budget, archive, and seed family `GP-MOM-VOL-001`.

It reuses:

- `quantlab.features.engine.compute_panel` for primitives (`momentum_5/10/20`, `rolling_std_20`, `rolling_mean_20`)
- `quantlab.labels.engine.compute_label_panel` + `forward_return(1)` at evaluation only
- `quantlab.alpha.ic.information_coefficient`
- `quantlab.orchestration.multiple_testing.family_correction`
- `quantlab.research.gate.evaluate_research_gate`
- `quantlab.research.integrity.evaluate_integrity`
- JSONL `ExperimentLedger`

`domain.research.SignalGenome` is unchanged. Simple trees may be mapped onto it; genetic search does not live in `quantlab.research.genome`.

## CLI

- `quantlab discovery list|inspect|search|…`
- Research aliases that do **not** steal Prompt 14: `quantlab research symbolic|genetic|alpha-discovery|novelty|expression|discovery-family`
- `quantlab research discover` remains the Prompt 14 hypothesis family runner

## Desktop

Discovery Lab (`quantlab.ui.pages.discovery_lab`) is a catalog viewer. It does not evaluate expressions or run GP in Qt.
