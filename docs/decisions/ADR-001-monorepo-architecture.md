# ADR-001 — Monorepo as a single Python package

## Context
The master instruction proposed `packages/core`, `domain`, `data`, … as separately installable packages.

## Problem
Twelve packages on Day 1 create circular-import risk, versioning noise, and slower iteration for one private lab.

## Options
1. uv/poetry workspaces with many packages
2. Single `src/quantlab` with internal modules mapped 1:1 to those packages
3. Nested `quant-lab/` directory inside this workspace

## Decision
Option 2. Workspace root **is** the repo. Module map: `quantlab.core`, `.domain`, `.data`, etc.

## Consequences
- Clean imports Day 1; split into published packages later if needed
- Apps: `src/quantlab/ui` is the PySide6 shell; `apps/api` and `apps/web` remain unused

## References
`docs/architecture/QUANT_LAB_ARCHITECTURE.md`
