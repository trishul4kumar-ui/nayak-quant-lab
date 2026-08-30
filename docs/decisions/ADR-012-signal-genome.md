# ADR-012 — Signal genome

## Context
Prompt 02 wants GENERATE/MUTATE/COMBINE later. TradingAgents and Qlib expressions are references, not copies.

## Problem
Opaque strings are not versionable research objects.

## Options
1. Python callables only
2. Small AST (feature / rank / zscore) + metadata/version
3. Full genetic programming now

## Decision
Option 2. No evolutionary search yet.

## Consequences
- Evaluated output remains `Signal`
- Genome is provenance, not an execution broker
