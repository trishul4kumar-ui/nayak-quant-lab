# ADR-046 — Production Shadow Validation

## Context

Prompt 35 requires evidence from observed market and broker state without creating
broker instructions. Existing `quantlab.shadow` owns paper OMS composition,
simulated fills, replay, and checkpoints.

## Decision

Add `quantlab.production_shadow` as a read-only composition and readiness layer.
It records time alignment, provenance, reconciliation, decision capture, shadow
replay evidence, incidents, and evidence labels. It reuses the existing shadow
engine rather than creating another OMS, TCA engine, portfolio engine, or ledger.

```text
LIVE_TRADING = FALSE
BROKER_WRITE_ENABLED = FALSE
NON_ROUTABLE = TRUE
SIMULATED FILL != BROKER FILL
```

Missing, mock, stale, or unverifiable evidence produces `BLOCKED`; it cannot be
silently replaced by synthetic data.

## Consequences

- `quantlab shadow-prod` is an evidence CLI, not an execution CLI.
- A production-data vendor and real broker observation must be explicitly
  configured before an assessment can progress beyond blocked evidence.
- This layer cannot certify or promote a release.
