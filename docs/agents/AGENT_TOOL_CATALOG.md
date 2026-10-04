# Agent tool catalog

| Tool | Canonical binding | Missing input behavior |
|---|---|---|
| freeze_snapshot | Inspect the existing frozen RealTimeSnapshot; does not poll a future feed | Reject missing/mismatched context |
| inspect_market | Frozen observations, whitelisted price evidence fields | Unknown values remain unknown |
| query_feature | `quantlab.features.engine.compute_value` | NOT_TESTED without frozen PIT history |
| query_knowledge | Catalogued, not bound in phase 39 | UNAVAILABLE |
| query_factor / query_regime | Catalogued, not bound in phase 39 | UNAVAILABLE |
| run_backtest / run_validation | Catalogued, not bound in phase 39 | UNAVAILABLE |
| econometrics / model / ensemble / portfolio / risk / TCA | Catalogued, not bound in phase 39 | UNAVAILABLE |

This catalog does not imply implemented adapters for every engine. Later phases
must add typed, PIT-bound adapters before calling those analyses. Model prose
cannot supply missing numeric evidence or silently mark an unavailable tool tested.

Use `python -m quantlab.cli agents tools` for the current binding state.
