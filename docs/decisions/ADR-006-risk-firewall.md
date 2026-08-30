# ADR-006 — Risk firewall

## Context
No reference fully implements a mandatory authorize() gate. Hummingbot executors have triple-barrier; QuantDinger documents high-risk API tests.

## Problem
AI, notebooks, and APIs will eventually propose trades.

## Options
1. Risk as optional analytics
2. Single `RiskFirewall.authorize(proposal) -> RiskDecision` required before OMS
3. LLM risk agent as authority

## Decision
Option 2. Fail closed if the firewall is unhealthy. AI cannot implement `authorize`.

## Consequences
- Every vertical-slice rebalance goes through the firewall
- Later limits (VaR, liquidity) plug into the same pipeline

## References
Master instruction §16; QuantDinger high-risk contracts
