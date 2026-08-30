# ADR-041 — Live Trading Certification, Promotion & Release Gate

## Context
Prompt 27 asked for an institutional certification/promotion/release-eligibility gate on QUANT LAB 2.6.0. Prompt 23 already owns `quantlab.certification`, CLI `quantlab validation`, and desktop nav `certify`. ADR-007 already names the original paper `BrokerGateway`.

## Decision
Add `quantlab.release` as the live-trading certification and promotion gate. Top-level CLI is `quantlab certification`. Desktop nav key is `promote` (**Certification & Promotion Lab**). Research aliases are `live-certification`, `live-readiness`, `promotion`, `release-gate`, and `certification-audit` so Prompt 23 aliases remain intact.

`CERTIFIED ≠ LIVE_ENABLED ≠ BROKER_CONNECTED`. There is no `LIVE` state. Safety requirements cannot be waived. AI cannot certify, approve, or waive. `LIVE_TRADING` remains false.

## Consequences
- Prompt 23 remains model-risk validation
- Prompt 05 remains the research gate
- Prompt 25 remains the live-trading safety gateway
- Release eligibility does not authorize live trading or broker writes
