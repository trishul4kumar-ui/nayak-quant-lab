# ADR-008 — AI permission model

## Context
TradingAgents uses LLM roles including Trader and Portfolio Manager. That is a research toy, not an OMS.

## Problem
How can AI help without authorizing money?

## Options
1. Agent places paper/live orders
2. Capability flags: READ_DATA, WRITE_RESEARCH, RUN_EXPERIMENT, RUN_BACKTEST; live order request always denied
3. No AI module

## Decision
Option 2. Module exists with permissions. No LLM client on Day 1.

## Consequences
- Future agents are tools with explicit scopes
- `REQUEST_LIVE_ORDER` cannot be granted to agents in config

## References
TradingAgents README; OpenBB MCP as a surface
