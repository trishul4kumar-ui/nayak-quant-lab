# ADR-030 — Knowledge graph and research memory

## Context
Prompt 16 asks QUANT LAB to answer: what has the lab learned about a hypothesis, where did it originate, what was tested, what failed, what survived, under which PIT snapshot and assumptions, and how is it related to other research?

Prompts 01–15 already own the PIT fabric, backtester, validation/gate, covariance, adaptive engine, JSONL ledger, orchestration control plane, and discovery engine. A second copy of any of those would fork scientific identity.

## Problem
Without a memory layer, failed candidates disappear, claims outrun evidence, AI summaries look like empirical results, and later data silently rewrites earlier conclusions.

## Options
1. Store research memory in a graph database (Neo4j)
2. Add `quantlab.knowledge` as a typed in-memory adjacency graph with JSON persistence beside the ledger
3. Treat the experiment ledger as the only memory and reconstruct genealogy ad hoc

## Decision
Option 2.

1. Knowledge is memory, not authority. It does not promote, trade, or override Prompt 05.
2. Failed research is retained. Deletes are `candidate_history_deleted` FAIL.
3. Evidence and historical claims are immutable. Supersession adds a new claim and a `SUPERSEDES` edge.
4. Lineage is first-class (`DERIVED_FROM`, `MUTATED_FROM`, …) and distinct from Prompt 14 orchestration lineage.
5. Relationships carry provenance (`source_experiment_id`, `evidence_id`, `confidence_basis`).
6. AI-generated content cannot be empirical evidence (`ai_evidence_confusion`).
7. The JSONL ledger remains canonical. Knowledge fields on `ExperimentRun` are optional defaults.
8. Prompt 14 remains the orchestration control plane (`quantlab research lineage` / `replicate` unchanged).
9. Prompt 15 remains the discovery engine. Discovery ingest records every candidate, including falsified ones.
10. A relational adjacency list is sufficient initially; hashes canonicalize node/edge order. No graph DB.
11. Synthetic evidence remains non-promotable (`synthetic_evidence_overpromotion`).
12. Historical claims are never silently mutated (`historical_claim_mutation`).

## Consequences
- `DISCOVERY ≠ CONFIRMATION ≠ VALIDATION ≠ LIVE TRADING`
- `KNOWLEDGE ≠ AUTHORITY`
- Integrity gains knowledge flags; unimplemented remain `NOT_TESTED`.
- Desktop Knowledge Lab is a query viewer of `quantlab.app`.

## References
Prompt 16; ADR-011, ADR-019, ADR-028, ADR-029
