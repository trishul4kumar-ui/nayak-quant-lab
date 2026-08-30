# ADR-035 — Institutional TCA, Execution Calibration & Capacity

## Context
Prompt 21 asks whether a strategy survives realistic execution, and at what capital it becomes fragile — without a second simulator or fabricated NSE ADV / bid-ask / Indian tax tables.

## Decision
Add `quantlab.tca` wrapping Prompt 13 execution models and Prompt 18 paper fills. Calibration is CALIBRATE → FREEZE → TEST. Capacity is policy-defined, not “largest capital with a positive backtest.” Observed vs modelled vs stressed TCA are distinct labels.

## Consequences
- Prompt 13 formulas remain canonical
- Missing volume ⇒ capacity `NOT_TESTED`, not infinite
- Fragility is not a promotion decision; Prompt 05 remains the gate
- `LIVE_TRADING` remains false
