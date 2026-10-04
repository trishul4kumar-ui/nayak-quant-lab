# Deterministic adjudication policy — 43-v1

Host-owned, frozen and hash-addressed. The agent gateway exposes no policy-edit
capability. The durable service accepts only the registered policy identity.
Changing a policy requires a new reviewed release; it never rewrites old decisions.

## Quantitative inputs

Only verified same-boundary tool results from the two independent role contexts
and their bounded debate are captured. Each measurement records its exact name,
canonical tool, unit, status and source result hashes. Scope-wide measurements
require `security_id=None`; security-specific values are not silently aggregated.
Conflicting duplicates become UNKNOWN (or FAIL if any source fails). Missing,
unbound or wrong-unit measurements never acquire passing values.

Required routes: validation (integrity, test-set integrity, walk-forward windows,
OOS Sharpe, robustness, parameter fragility, canonical contradiction); backtest
(next-bar fill); econometrics (statistics, multiple testing, hypothesis count);
factor/regime (independence/fit); model/ensemble evaluation; TCA (expected edge,
estimated costs, 20-bps survival, liquidity); risk (risk-clear).
Booleans use 0/1, counts positive integers, proportions [0,1], and costs positive bps.
Gross edge may be negative. Gross edge and costs must share a canonical result
artifact before subtraction. Descriptive momentum, beta or regime labels are not
aliases for any of these validation metrics.

The existing canonical `evaluate_research_gate` produces a frozen typed gate
artifact, including all reason statuses and source measurement identities. A missing
prerequisite leaves this gate NOT_TESTED; the decision verifier recomputes it.

## Score normalization

Each valid measurement is clipped linearly to [0,1], then multiplied by its fixed
weight and 100. Missing/failed components earn zero; weights are never redistributed.

| Component | Range | Weight |
|---|---|---|
| Research gate | Candidate = 1 | .10 |
| OOS Sharpe | 0–2 | .16 |
| Gross expected edge | 0–20 bps | .10 |
| Robustness | 0–1 | .12 |
| Factor independence | 0–1 | .10 |
| Regime fit | 0–1 | .08 |
| Net edge after modeled costs | 0–20 bps | .12 |
| Liquidity | 0–1 | .12 |
| Canonical contradiction | Inverse 0–1 | .10 |
| Agent calibration | Unavailable until Phase 48 | 0 |

These are conservative versioned research-policy defaults, not empirically optimized
trading thresholds. Raw confidence, critique severity, rhetorical claims, memo
stances and preferred exposure contribute no mathematical score.

## Abstention and precedence

All required evidence must PASS for both roles. Hard blockers override high scores:
invalid/stale data or incomplete debate; failed required validation/integrity or
rejected/weak research gate; net edge ≤2 bps (including edge ≤cost); material canonical
contradiction ≥.5; missing evidence; unclear/rejected risk; liquidity <.5 or unknown;
synthetic/replay not current market evidence. The displayed outcome identifies the
highest-priority blocking family while retaining **all** blocker codes.

With no blockers, a maximum score below 65 gives LOW_CONFIDENCE; an absolute Bull/Bear
gap ≤8 points gives CONFLICTED. Otherwise the stronger evidence side is dominant.
Every non-dominant outcome has `no_trade=true`. Dominance permits further research
processing only: **every decision has execution_authority=false**.

Use the frozen evaluation clock, never ambient time in the scoring function. TTL
and a maximum 300-second snapshot age apply; replay bypasses market-age comparison
but is still explicitly no-trade. Historical UI records are marked expired rather
than silently treated as current approvals.

## Reproducibility and audit

Full decision/input hashes include immutable lineage and creation clocks. The separate
`result_hash` includes policy, quantitative components, outcome, blockers and warnings,
not narrative or lineage hashes. Prose restyling therefore cannot change the numeric
result, while changed source artifacts correctly produce new lineage identities.
Loading a saved decision verifies its original transcript, captures its original
inputs again, and recomputes the decision byte-for-byte. No model or broker is called.

## Current integration limitation

Only the five adapters documented in AGENT_TOOL_CATALOG.md are currently bound.
They do **not** provide the complete adjudication metric set. Real desk evaluations
therefore remain blocked/no-trade, not falsely complete or profitable. Passing
dominance branches in unit tests use explicitly constructed fixture measurements;
those tests do not attest real-market validation, liquidity, risk or live readiness.
