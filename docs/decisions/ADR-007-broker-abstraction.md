# ADR-007 — Broker abstraction

## Context
VN.Py Gateway, Hummingbot Connector, OpenAlgo unified Indian API.

## Problem
Zerodha/Kite and OpenAlgo must not appear in strategy code.

## Options
1. Call Kite from strategies
2. `BrokerGateway` protocol + PaperGateway now; OpenAlgo later
3. Depend on OpenAlgo Python as the domain

## Decision
Option 2. Live disabled. Paper gateway records intended orders only.

## Consequences
- OpenAlgo becomes an adapter in Phase 8
- Idempotent client order IDs from `quantlab.core.identifiers`

## References
VN.Py `trader/gateway.py`; OpenAlgo `broker/`
