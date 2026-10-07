# Trade candidate schema and lifecycle

`TradeCandidatePacket` carries frozen references to snapshot, Bull memo, Bear memo,
debate, adjudication, level plan, research gate, security mapping, and candidate policy.
It also records data quality/freshness, raw and optionally released calibrated confidence,
evidence summaries, blockers, warnings, and explicitly false execution authority.

```text
DRAFT -> GATHERING_EVIDENCE -> VALIDATING -> READY_FOR_REVIEW
                                           -> BLOCKED
READY_FOR_REVIEW -> WATCH | REJECTED | EXPIRED | PAPER_ELIGIBLE | SHADOW_ELIGIBLE
```

`PAPER_ELIGIBLE` and `SHADOW_ELIGIBLE` are research lifecycle states, not permission
to route an order. A refreshed candidate is a new immutable artifact; history is never
overwritten. Stale or invalid packets must be rebuilt from verified upstream data.
