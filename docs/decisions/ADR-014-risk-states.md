# ADR-014 — Risk states

## Context
Prompt 02 defines NORMAL → CAUTION → RESTRICTED → HALT → EMERGENCY.

## Problem
A healthy firewall that still allows orders during a halt is not a firewall.

## Options
1. Limits only
2. Explicit RiskState; HALT/EMERGENCY reject all new proposals
3. LLM sets the state

## Decision
Option 2. Default NORMAL. Limits remain configurable.

## Consequences
- Tests cover halt fail-closed
- Drawdown-driven transitions deferred
