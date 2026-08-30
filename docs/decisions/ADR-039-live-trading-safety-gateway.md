# ADR-039 — Live Trading Safety Gateway

## Context
Prompt 24 already occupied ADR-038 (production paper / shadow). Prompt 25 specified ADR-038 for the safety gateway; this ADR is numbered **039** to preserve the existing shadow decision record.

Prompt 25 asks: if an execution request were presented to the live boundary, is it authorized/valid/reconciled/risk-compliant/healthy/safe — or must it be rejected? It is **not** live trading.

## Decision
Add `quantlab.safety` with an explicit state machine, G0–G15 gates, immutable hashed authorization, kill switches, reconciliation/staleness/idempotency barriers, human authorization, and emergency mode. Top-level CLI is `quantlab safety`. Desktop nav key is `safety` (**Safety & Control Lab**). `LIVE_TRADING` remains false. G15 always BLOCK.

## Consequences
- Authorization is not a broker submit
- AI cannot authorize, unkill, or disable gates
- Human approval cannot bypass other gates
- Unknown safety state is BLOCK, never PASS
- Prompt 05 remains the research gate; Prompt 23 remains certification; Prompt 24 remains shadow
