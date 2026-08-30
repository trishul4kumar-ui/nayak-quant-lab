# QUANT LAB — CURSOR ENGINEERING PROMPT 16
## Alpha Knowledge Graph, Research Memory & Hypothesis Genealogy Engine

**Target release:** QUANT LAB 1.6.0  
**Current base:** QUANT LAB 1.5.0  
**Role:** Research-memory and scientific-provenance layer  
**Live trading:** MUST remain `false`

---

## 1. Mission

Implement a **Knowledge Graph, Research Memory & Hypothesis Genealogy Engine** on top of Prompts 01–15.

It must answer:

> What has QUANT LAB learned about a hypothesis, where did it originate, what was tested, what failed, what survived, under which PIT snapshot and assumptions, and how is it related to other research?

This is **not** a new alpha engine, backtester, optimizer, broker, OMS, PIT fabric, FDR engine, or research gate.

Preserve:

```text
DATA ≠ FEATURE ≠ FACTOR ≠ ALPHA ≠ REGIME ≠ MODEL
≠ ADAPTIVE LEARNER ≠ ENSEMBLE ≠ PORTFOLIO ≠ ORDER
≠ EXECUTION ≠ EXPERIMENT ≠ HYPOTHESIS
≠ DISCOVERY ≠ EVIDENCE ≠ KNOWLEDGE
```

A discovered expression is a hypothesis. Evidence-backed knowledge requires explicit provenance.

---

# 2. Hard architectural constraints

Do NOT rewrite Prompts 01–15.

Reuse:

- Prompt 04 PIT fabric
- Prompt 05 backtest/validation/research gate
- Prompt 06 feature/alpha research
- Prompt 07 portfolio construction
- Prompt 08 factor/risk engine
- Prompt 09 regime engine
- Prompt 10 adaptive learning
- Prompt 11 statistical learning
- Prompt 12 ensemble/meta-alpha
- Prompt 13 execution research
- Prompt 14 orchestration
- Prompt 15 genetic/symbolic discovery
- existing JSONL ledger
- existing integrity framework
- existing hashes/configuration identities
- existing `quantlab.app`
- existing desktop architecture

There must still be:

```text
ONE PIT FABRIC
ONE BACKTESTER
ONE VALIDATION/GATE
ONE COVARIANCE ENGINE
ONE ADAPTIVE ENGINE
ONE LEDGER
ONE ORCHESTRATION CONTROL PLANE
ONE DISCOVERY ENGINE
```

Prompt 16 is a **knowledge layer over them**.

---

# 3. Package

Create:

```text
src/quantlab/knowledge/
├── __init__.py
├── entities.py
├── graph.py
├── lineage.py
├── evidence.py
├── provenance.py
├── relationships.py
├── similarity.py
├── genealogy.py
├── status.py
├── memory.py
├── query.py
├── indexing.py
├── snapshots.py
├── serialization.py
└── integrity.py
```

Keep `__init__.py` thin. Avoid circular imports.

---

# 4. Knowledge graph domain

Implement typed nodes.

Base fields:

```text
node_id
node_type
canonical_identity
version
created_at
updated_at
status
source
config_hash
content_hash
metadata
```

Required node types:

```text
HYPOTHESIS
EXPRESSION
FEATURE
FACTOR
ALPHA
MODEL
ADAPTIVE_LEARNER
ENSEMBLE
REGIME
PORTFOLIO
EXPERIMENT
DISCOVERY_RUN
EVIDENCE
FALSIFICATION
REPLICATION
VALIDATION
DATASET_SNAPSHOT
EXECUTION_ASSUMPTION
RESEARCH_RESULT
RESEARCH_CLAIM
```

Reference existing domain identities instead of duplicating domain objects.

---

# 5. Hypothesis genealogy

Create a knowledge-level `HypothesisRecord`:

```text
hypothesis_id
title
statement
formal_expression
expected_direction
economic_rationale
mathematical_rationale
source_type
parent_hypothesis_id
discovery_id
pre_registration_id
created_at
status
```

Statuses:

```text
PROPOSED
PRE_REGISTERED
UNDER_TEST
SUPPORTED
PARTIALLY_SUPPORTED
FALSIFIED
REJECTED
REPLICATED
VALIDATED
STALE
SUPERSEDED
DUPLICATE
INCONCLUSIVE
NOT_TESTED
```

Never treat `SUPPORTED` as equivalent to profitable.

Genealogy edges:

```text
DERIVED_FROM
MUTATED_FROM
CROSSED_FROM
SIMPLIFIED_FROM
GENERALIZED_FROM
SPECIALIZED_FROM
RESIDUALIZED_FROM
ENSEMBLED_FROM
STACKED_FROM
FALSIFIED_BY
REPLICATED_BY
SUPERSEDES
DUPLICATES
CONTRADICTS
SUPPORTS
```

Prompt 15 candidate ancestry must never disappear when candidates are pruned.

---

# 6. Expression identity

Integrate with Prompt 15 typed AST.

Store:

```text
raw_expression
canonical_expression
expression_hash
complexity
operator_count
depth
feature_dependencies
constant_parameters
normalization_requirements
```

Canonicalize only mathematically safe equivalences.

Detect:

```text
IDENTICAL
HIGH_REDUNDANCY
RELATED
WEAKLY_RELATED
DISTINCT
UNKNOWN
```

Do not infer statistical independence from syntactic difference.

---

# 7. Evidence

Create immutable `EvidenceRecord`:

```text
evidence_id
experiment_id
hypothesis_id
dataset_id
snapshot_checksum
config_hash
result_type
metric
metric_value
sample_size
coverage
train_period
validation_period
test_period
regime_context
execution_assumption
integrity_status
gate_status
created_at
```

Evidence types:

```text
DISCOVERY_EVIDENCE
IN_SAMPLE_EVIDENCE
OOS_EVIDENCE
WALK_FORWARD_EVIDENCE
ROBUSTNESS_EVIDENCE
STATISTICAL_EVIDENCE
EXECUTION_EVIDENCE
REGIME_EVIDENCE
RISK_EVIDENCE
REPLICATION_EVIDENCE
FALSIFICATION_EVIDENCE
ABLATION_EVIDENCE
SENSITIVITY_EVIDENCE
NULL_EVIDENCE
```

Evidence state:

```text
PASS
FAIL
WARN
NOT_TESTED
```

Never convert `NOT_TESTED` to PASS.

---

# 8. Provenance

Every research assertion must trace to:

```text
dataset snapshot
snapshot checksum
available-time policy
universe definition
feature identity/version
alpha identity/version
model identity/version
experiment identity
search-space identity
selection policy
backtest configuration
cost assumptions
execution assumptions
validation protocol
multiple-testing family
software version
config hash
```

The system must answer:

> Why does QUANT LAB believe this?

and:

> Which exact computation produced the evidence?

---

# 9. Research claims

Implement `ResearchClaim`.

Example:

```text
CLAIM:
20-day momentum showed positive OOS IC
under the tested research protocol.

SUPPORT:
EVIDENCE-017

DATA:
SNAPSHOT-003

STATUS:
WARN

LIMITATIONS:
synthetic data
no official holidays
no calibrated ADV
```

Claim status:

```text
UNSUPPORTED
PRELIMINARY
SUPPORTED
REPLICATED
VALIDATED
CONTRADICTED
FALSIFIED
```

Claims must never be stronger than their evidence.

Synthetic evidence cannot become validated market knowledge.

---

# 10. Contradiction engine

Detect conflicting claims without silently resolving them.

Example:

```text
H1: momentum is positive
H2: momentum is negative
```

or:

```text
H1: alpha survives execution
H2: alpha disappears after execution costs
```

Create:

```text
CONTRADICTS
```

relationships and preserve both evidence chains.

Contradiction is a research question, not an automatic winner selection.

---

# 11. Research memory

Persist:

```text
WHAT WAS TRIED
WHAT WAS FOUND
WHAT FAILED
WHY IT FAILED
WHAT DATA WAS USED
WHAT ASSUMPTIONS WERE USED
WHAT WAS NOT TESTED
WHAT WAS SELECTED
WHAT WAS REJECTED
WHAT WAS REDUNDANT
WHAT WAS FALSIFIED
WHAT WAS REPLICATED
```

The system should answer:

```text
Have we already tested something similar?

Which momentum expressions failed?

Which alpha families are redundant?

Which candidates failed because of execution?

Which hypotheses have never been replicated?

Which discoveries depend on synthetic data?

What was tested under each regime?

How many candidates were searched?
```

---

# 12. Dead-end memory

Failed research is first-class knowledge.

Example:

```text
DEAD_END-042

Hypothesis:
volatility-adjusted momentum

Failure:
OOS effect disappeared

Execution:
net edge negative

Regime:
effect concentrated in one regime

Conclusion:
not robust
```

Do not delete failed candidates.

Do not allow future discovery to blindly repeat an identical failed region.

However, do not automatically forbid re-testing; return:

```text
KNOWN
RELATED
NOVEL
UNKNOWN
```

and let orchestration decide.

---

# 13. Replication graph

Support:

```text
EXACT_REPLICATION
TEMPORAL_REPLICATION
DATASET_REPLICATION
UNIVERSE_REPLICATION
REGIME_REPLICATION
EXECUTION_REPLICATION
METHODOLOGICAL_REPLICATION
```

A replication must identify:

```text
original_hypothesis
original_experiment
replication_experiment
dataset_difference
time_period_difference
feature_difference
execution_difference
result_comparison
```

Do not call the same snapshot/protocol repeated execution an independent replication.

---

# 14. Falsification graph

Represent:

```text
HYPOTHESIS
   ↓
FALSIFICATION ATTEMPT
   ├── sign reversal
   ├── null permutation
   ├── feature substitution
   ├── cost stress
   ├── regime split
   ├── OOS test
   └── execution stress
```

Reuse Prompts 14–15 machinery.

Do not create a second falsification engine unnecessarily.

---

# 15. Alpha families

Represent genealogy:

```text
MOMENTUM FAMILY
├── momentum_5
├── momentum_10
├── momentum_20
├── momentum_60
├── rank(momentum_20)
├── zscore(momentum_20)
├── volatility_adjusted_momentum
└── regime_conditional_momentum
```

Track:

```text
parent
descendants
siblings
mutations
redundant members
failed members
surviving members
```

This is essential for degrees-of-freedom accounting.

---

# 16. Search degrees of freedom

Integrate with Prompt 14.

Track:

```text
family_id
search_space_id
candidate_count
tested_count
rejected_count
falsified_count
selected_count
pruned_count
duplicate_count
stopping_reason
selection_policy
```

Discarded candidates remain part of the historical search record.

Never erase search history to make a selected result look cleaner.

---

# 17. Lineage traversal

Support:

```text
DISCOVERY_RUN
   ↓
EXPRESSION
   ↓
FEATURES
   ↓
DATASET_SNAPSHOT
   ↓
EXPERIMENT
   ↓
BACKTEST
   ↓
VALIDATION
   ↓
EXECUTION_RESEARCH
   ↓
GATE
   ↓
RESEARCH_CLAIM
```

Reverse traversal must answer:

> Why was this alpha rejected?

> Where did this hypothesis originate?

> What evidence supports this claim?

---

# 18. Temporal knowledge

Research memory must itself be time-aware.

Track:

```text
knowledge_as_of
evidence_as_of
dataset_as_of
created_at
superseded_at
```

A conclusion based on data through T must not silently become a conclusion about later data.

Historical claims are never mutated.

Use:

```text
OLD CLAIM
   ↓
SUPERSEDES
   ↓
NEW CLAIM
```

---

# 19. Immutable knowledge snapshots

Create:

```text
knowledge_snapshot_id
created_at
graph_hash
node_count
edge_count
software_version
schema_version
```

Historical reports must be reproducible against the snapshot available when created.

Canonicalize node/edge ordering for deterministic hashes.

---

# 20. Evidence profile

Do not create an arbitrary opaque confidence score.

Expose:

```text
PIT integrity
OOS evidence
walk-forward evidence
execution evidence
statistical evidence
multiple-testing status
replication evidence
regime stability
risk stability
data quality
sample size
coverage
```

Example:

```text
PIT              PASS
OOS              PASS
Execution        WARN
Multiple testing PASS
Replication      NOT_TESTED
Regime stability WARN
Data quality     WARN

Overall:
WARN
```

Prompt 05 remains the only promotion gate.

---

# 21. Knowledge query API

Implement:

```text
find_hypothesis()
find_related_hypotheses()
find_similar_expression()
find_alpha_family()
find_lineage()
find_evidence()
find_failures()
find_dead_ends()
find_replications()
find_contradictions()
find_research_claims()
find_dependencies()
find_dependents()
find_by_dataset()
find_by_regime()
find_by_feature()
find_by_factor()
find_by_experiment()
find_by_status()
```

Index:

```text
node_type
status
hypothesis_id
experiment_id
family_id
expression_hash
canonical_identity
dataset_id
created_at
relationship_type
```

---

# 22. CLI

Add:

```text
quantlab knowledge list
quantlab knowledge inspect <id>
quantlab knowledge search <query>
quantlab knowledge graph <id>
quantlab knowledge lineage <id>
quantlab knowledge evidence <id>
quantlab knowledge status <id>
quantlab knowledge similar <id>
quantlab knowledge family <id>
quantlab knowledge failures <id>
quantlab knowledge replications <id>
quantlab knowledge contradictions
quantlab knowledge snapshot
quantlab knowledge diff <snapshot_a> <snapshot_b>
quantlab knowledge report <hypothesis_id>
quantlab knowledge export
```

Aliases:

```text
quantlab research knowledge
quantlab research lineage
quantlab research genealogy
quantlab research dead-ends
quantlab research replication
quantlab research contradictions
quantlab research similarity
quantlab research evidence
quantlab research alpha-family
```

Existing commands must remain unchanged.

---

# 23. Desktop — Knowledge Lab

Add:

```text
Knowledge Lab
├── Overview
├── Hypotheses
├── Alpha Families
├── Genealogy
├── Evidence
├── Failures
├── Replications
├── Contradictions
├── Similarity
├── Research Claims
└── Snapshots
```

UI uses `quantlab.app`.

Qt must NOT:

- parse Parquet directly
- query DuckDB directly
- fit models
- run GP
- compute alpha
- calculate covariance
- run backtests
- modify the ledger directly
- place orders

Add graph visualization with filtering by:

```text
status
date
experiment family
evidence quality
relationship
```

---

# 24. AI boundary

Prepare for future AI-assisted research.

AI may:

```text
summarize evidence
suggest hypotheses
find related research
identify unexplored regions
suggest falsification tests
explain genealogy
generate research questions
```

AI must NOT:

```text
override PIT
override integrity
override research gate
rewrite historical evidence
delete failed hypotheses
hide search degrees of freedom
alter empirical results
promote synthetic alpha
request live orders
bypass risk controls
```

Label AI content:

```text
AI_GENERATED_HYPOTHESIS
AI_GENERATED_SUMMARY
AI_GENERATED_RESEARCH_SUGGESTION
```

AI-generated content is never empirical evidence.

Design service boundaries so a future research agent operates:

```text
OBSERVE
→ QUERY KNOWLEDGE
→ FORM HYPOTHESIS
→ CHECK NOVELTY
→ PRE-REGISTER
→ RUN EXPERIMENT
→ COLLECT EVIDENCE
→ FALSIFY
→ REPLICATE
→ UPDATE KNOWLEDGE
```

---

# 25. Persistence

Prefer the existing local persistence conventions.

Do not introduce a graph database unless clearly justified.

An indexed relational adjacency model is preferred initially.

Conceptual tables:

```text
knowledge_nodes
knowledge_edges
hypotheses
evidence
claims
genealogy
replications
falsifications
similarity_records
knowledge_snapshots
```

Every edge contains:

```text
edge_id
source_id
target_id
relationship_type
created_at
source_experiment_id
evidence_id
confidence_basis
metadata
```

Relationships themselves require provenance where applicable.

---

# 26. Integrity

Add:

```text
knowledge_provenance_break
evidence_without_experiment
claim_without_evidence
claim_overstates_evidence
lineage_break
candidate_history_deleted
duplicate_identity_collision
snapshot_mutation
historical_claim_mutation
future_knowledge_leak
future_claim_context
replication_same_data
contradiction_hidden
search_degree_of_freedom_loss
synthetic_evidence_overpromotion
ai_evidence_confusion
```

Semantics:

```text
None → NOT_TESTED
invalid/leaky → FAIL
verified → PASS
```

Never convert unknown to PASS.

---

# 27. Change detection

Compare knowledge snapshots:

```text
quantlab knowledge diff <A> <B>
```

Return:

```text
new hypotheses
new evidence
new failures
new replications
new contradictions
superseded claims
changed statuses
new alpha families
new redundancy relationships
```

---

# 28. Research report

`quantlab knowledge report <hypothesis_id>` must answer:

```text
WHAT:
What hypothesis?

WHY:
Why was it tested?

DATA:
Which exact PIT snapshot?

METHOD:
Which experiment?

SEARCH:
How many candidates?

SELECTION:
How was selection performed?

RESULT:
What happened?

ROBUSTNESS:
What survived?

EXECUTION:
Did costs change the conclusion?

FALSIFICATION:
What failed?

REPLICATION:
Was it independently replicated?

LIMITATIONS:
What remains NOT_TESTED?

STATUS:
What does the evidence justify?

LINEAGE:
Where did it originate?
```

Never invent missing evidence.

---

# 29. Testing

Create:

```text
tests/knowledge/
├── test_entities.py
├── test_identity.py
├── test_lineage.py
├── test_genealogy.py
├── test_evidence.py
├── test_claims.py
├── test_similarity.py
├── test_replication.py
├── test_contradictions.py
├── test_snapshots.py
├── test_temporal_integrity.py
├── test_degree_of_freedom.py
├── test_discovery_integration.py
├── test_orchestration_integration.py
├── test_ledger_integration.py
└── test_queries.py
```

Mandatory adversarial tests:

1. Delete a failed discovery candidate.
2. Mutate historical evidence.
3. Attach evidence to the wrong experiment.
4. Use future evidence for an earlier claim.
5. Label identical data as independent replication.
6. Change expression without changing identity.
7. Detect mathematically equivalent expressions.
8. Hide discarded candidates.
9. Promote synthetic evidence.
10. Treat AI text as empirical evidence.
11. Create contradictory claims.
12. Supersede a claim without preserving the old claim.
13. Mutate a knowledge snapshot.
14. Break mutation genealogy.
15. Create an unsupported claim.

All must fail safely.

---

# 30. Determinism

Given identical:

```text
dataset snapshot
software version
config
experiment
knowledge snapshot
```

the same graph hash must be generated.

Canonicalize:

- node ordering
- edge ordering
- metadata serialization

Do not include volatile UI state in hashes.

---

# 31. Documentation

Create:

```text
docs/architecture/KNOWLEDGE_GRAPH_ENGINE.md
docs/architecture/RESEARCH_MEMORY.md
docs/architecture/HYPOTHESIS_GENEALOGY.md
docs/architecture/EVIDENCE_PROVENANCE.md
docs/research/KNOWLEDGE_MANAGEMENT.md
docs/research/RESEARCH_MEMORY.md
docs/research/ALPHA_GENEALOGY.md
docs/research/RESEARCH_EVIDENCE.md
docs/decisions/ADR-030-knowledge-graph-research-memory.md
```

Update:

```text
README.md
BACKLOG.md
LOCAL_RUN.md
architecture map
```

---

# 32. ADR-030

Document:

1. Separation of knowledge from experiments.
2. Retention of failed research.
3. Immutable evidence.
4. First-class lineage.
5. Provenance-bearing relationships.
6. AI cannot create empirical evidence.
7. Existing ledger remains canonical.
8. Prompt 14 remains orchestration control plane.
9. Prompt 15 remains discovery engine.
10. Why a relational graph is sufficient initially.
11. Synthetic evidence remains non-promotable.
12. Historical claims are never silently mutated.

---

# 33. Version

Update:

```text
1.5.0 → 1.6.0
```

Preserve backward compatibility with Prompts 01–15 persisted records.

Old ledger rows must continue to load.

---

# 34. Definition of Done

All must pass:

## Architecture

- `quantlab.knowledge` implemented.
- No duplicate PIT fabric.
- No duplicate backtester.
- No duplicate gate.
- No duplicate ledger.
- No broker dependency.
- No live path.

## Knowledge

- Typed nodes.
- Typed edges.
- Deterministic identities.
- Evidence provenance.
- Immutable historical records.
- Genealogy.
- Claims.
- Contradictions.
- Replication.
- Similarity.
- Snapshots.

## Discovery integration

- Prompt 15 candidates become knowledge records.
- Candidate lineage preserved.
- Degrees of freedom preserved.
- Redundancy recorded.
- Failed candidates retained.
- Falsification linked.

## Orchestration integration

- Prompt 14 experiments linked.
- Search spaces linked.
- Selection policies linked.
- Candidate counts preserved.
- Multiple-testing context preserved.

## Desktop

- Knowledge Lab implemented.
- Graph viewer works.
- Evidence viewer works.
- Genealogy works.
- Failure/dead-end viewer works.
- UI cannot bypass controls.

## Quality

- Full existing test suite passes.
- New tests pass.
- Integrity tests pass.
- UI offscreen tests pass.
- Ruff clean.
- Mypy strict clean.
- Deterministic snapshot test passes.
- Historical mutation test passes.
- Synthetic promotion test passes.
- AI evidence confusion test passes.

---

# 35. Final engineering report

After implementation, report:

```text
QUANT LAB VERSION:
PROMPT 16 STATUS:

NEW MODULES:
NEW CLI COMMANDS:
NEW DESKTOP FEATURES:

KNOWLEDGE NODES:
KNOWLEDGE EDGES:
GENEALOGY:
EVIDENCE PROVENANCE:
REPLICATION:
FALSIFICATION:
SIMILARITY:
SNAPSHOTS:

INTEGRITY CHECKS:
TEST COUNT:
RUFF:
MYPY:
LIVE_TRADING:
PROMPTS 01–15 REGRESSION:
DOCUMENTATION:

KNOWN NOT_TESTED:
KNOWN LIMITATIONS:
```

Demonstrate:

### A — Genealogy

```text
Prompt 15 discovery
→ expression
→ hypothesis
→ experiment
→ evidence
→ falsification
→ claim
```

### B — Dead end

Show a failed candidate remaining searchable and explain why its existence prevents blind rediscovery.

### C — Contradiction

Create two conflicting research results and demonstrate that both evidence chains remain intact.

---

# 36. Final directive

Do not optimize for feature count.

Optimize for:

```text
SCIENTIFIC TRACEABILITY
REPRODUCIBILITY
FALSIFIABILITY
PROVENANCE
TEMPORAL CORRECTNESS
SEARCH-SPACE ACCOUNTING
HISTORICAL IMMUTABILITY
RESEARCH MEMORY
```

The laboratory must remember both:

```text
WHAT WORKED
```

and:

```text
WHAT DID NOT WORK
```

The latter is equally valuable.

Target architecture:

```text
                         QUANT LAB
                            │
                  ┌─────────┴─────────┐
                  │   RESEARCH MEMORY │
                  │    PROMPT 16      │
                  └─────────┬─────────┘
                            │
       ┌────────────────────┼────────────────────┐
       ↓                    ↓                    ↓
  HYPOTHESIS           EVIDENCE             GENEALOGY
       │                    │                    │
       └────────────────────┼────────────────────┘
                            ↓
                    RESEARCH ORCHESTRATION
                         PROMPT 14
                            ↓
                    ALPHA DISCOVERY
                         PROMPT 15
                            ↓
              FEATURES / MODELS / ENSEMBLES
                            ↓
                  PORTFOLIO / RISK / EXECUTION
                            ↓
                 BACKTEST + VALIDATION
                            ↓
                     RESEARCH GATE
                            ↓
                         LEDGER
```

**Knowledge is memory, not authority.**

**Evidence is immutable.**

**Failed hypotheses are preserved.**

**AI suggestions are not evidence.**

**Discovery is not confirmation.**

**Confirmation is not validation.**

**Validation is not live trading.**

`LIVE_TRADING=false` remains mandatory.
