# ADR-038 — Production Paper Trading & Shadow Execution Engine

## Context
Prompt 24 asks: if QUANT LAB were operating in production right now, what would it decide, what orders would it intend, what would those orders hypothetically experience, and how would the portfolio evolve — without sending a single broker order.

## Decision
Add `quantlab.shadow` as an operational composition layer around Prompt 18 paper OMS, Prompt 13 execution-research fills, Prompt 20 weekday calendar, Prompt 21 TCA, Prompt 19 monitoring, and Prompt 23 certification. Shadow orders are distinct from paper orders and are never routable. Modes are explicit (`OFF | RESEARCH_PAPER | PAPER | SHADOW | PAUSED | HALTED | ERROR | RECOVERY`). `LIVE_TRADING` remains false. Top-level CLI is `quantlab shadow`. Desktop nav key is `shadow` (**Shadow Trading Lab**).

## Consequences
- Paper profit is not validated alpha; shadow execution is not broker execution
- Synthetic seed data remains labelled and cannot be `REAL_MARKET`
- Production `PAPER`/`SHADOW` without eligible certification does not silently run as production
- HALT rejects new exposure and is not AUTO-LIQUIDATE
- Prompt 05 remains the research gate; Prompt 23 remains certification authority
