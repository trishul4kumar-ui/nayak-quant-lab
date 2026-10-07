# Phase 45 — Trade Candidate and Evidence Packet

## Delivered local research surface

- Immutable, hash-addressed `CandidateBuildInput`, `TradeCandidatePacket`,
  evidence summaries, freshness records, and lifecycle events.
- Candidate lifecycle is bounded to research, watch, paper, and shadow states.
  There is deliberately no `LIVE_ELIGIBLE` state.
- Candidate ranking is attention-only. It accepts no quantity, order, broker, or
  account fields and grants no execution authority.
- Freshness checks block a packet on expiry, price deviation, changed regime,
  liquidity failure, changed security mapping/corporate action, or validation expiry.
- The native Trade Queue displays persisted packets, filters them, and opens the
  review-only Phase 46 console. It does not create orders.

## Boundary

The packet contracts exist locally, but this phase does not manufacture research
inputs, prices, validations, or calibration. An incomplete, unknown, failed, or
not-tested evidence item blocks readiness. Real upstream lineage must be persisted
and verified before a production workflow could construct a packet.

## Acceptance pending

Focused contract, lifecycle, freshness, and UI smoke checks pass locally during the
45–48 batch. Consolidated full-suite and cloud CI evidence is still required before
this phase is accepted.
