# ADR-040 — Production Operational Control Plane

## Context
Prompt 26 specified ADR-039 for ops, but ADR-039 is the live-trading safety gateway (Prompt 25). This ADR is numbered **040**.

Prompt 26 asks: if QUANT LAB were running as a production system, is the process alive, configured, healthy, recoverable, and observable — without placing a live order?

## Decision
Add `quantlab.ops` as an operations control plane: supervisor, config/env/secrets, health/readiness wrapping `quantlab.app.health`, checksummed backup/restore, clock/disk, release identity, and `quantlab ops doctor`. Desktop nav key is `ops` (**Operations Control Lab**), distinct from existing `system`. `LIVE_TRADING` remains false.

## Consequences
- Ops does not absorb Prompts 05, 23, 24, or 25
- Fatal states require explicit recovery
- Secrets never appear in leakable channels
- Scheduler cannot invoke live trading
