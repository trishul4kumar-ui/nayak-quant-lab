# ADR-045 — Deterministic Shadow Validation, Replay & Digital Twin

## Context
Prompt 31 asked for a deterministic shadow/replay twin. Prompt 24 already owns `quantlab.shadow`, CLI `quantlab shadow`, and nav `shadow`. This ADR is therefore **045**, and the twin must not overwrite Prompt 24.

## Decision
Add `quantlab.digital_twin`. Compose Prompt 29 snapshots, Prompt 30 decisions, Prompt 18 paper accounting, Prompt 13/21 simulated fills, and Prompt 19 monitoring hashes. Do not duplicate OMS, TCA, backtester, or ledger.

```text
LIVE_TRADING = FALSE
BROKER_WRITE_ENABLED = FALSE
SHADOW ≠ PAPER ≠ LIVE
DIGITAL TWIN ≠ BROKER
SIMULATED FILL ≠ BROKER CONFIRMATION
```

Modes: `HISTORICAL_REPLAY | REALTIME_SHADOW | PAPER_REPLAY | FAILURE_INJECTION | COUNTERFACTUAL | DETERMINISM_TEST` — all non-routable.

Top-level CLI is `quantlab twin` (not `quantlab shadow`). Desktop nav key is `twin` (**Digital Twin / Shadow Lab**).

Write/order paths raise `TwinRoutingError`.

## Consequences
- Prompt 24 Shadow Trading Lab remains
- Replay identity: same inputs → same hashes, else `ReplayMismatch`
- Counterfactuals are labelled and must not contaminate observed shadow results
- This engine does not certify itself and does not talk to a broker
