# Phase 50 — Intraday / scalping research

The local foundation uses immutable PIT tick/depth observations, deterministic top-of-book
features, versioned cost-required strategy definitions, and caller-driven replay with explicit
latency/gap injection. The hot path imports no agent or broker client. Stale, malformed, or
missing-depth inputs abstain; a signal has explicitly false execution authority.

This is research infrastructure, not a claim of predictive scalp alpha or a live feed adapter.
Provider entitlement and current WebSocket behavior must be independently verified before any
real-observation integration.
