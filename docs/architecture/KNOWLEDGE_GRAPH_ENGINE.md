# Knowledge Graph Engine

**Status:** Prompt 16 / ADR-030  
**Version:** 1.6.0

Prompt 16 is a **research-memory layer**. It records what QUANT LAB has learned about a hypothesis: origin, tests, failures, survivors, PIT snapshot, and relations. It is not a second fabric, backtester, gate, FDR engine, discovery engine, orchestration plane, or ledger.

```text
KNOWLEDGE ≠ AUTHORITY
EVIDENCE IS IMMUTABLE
FAILED HYPOTHESES ARE PRESERVED
AI SUGGESTIONS ARE NOT EVIDENCE
DISCOVERY ≠ CONFIRMATION ≠ VALIDATION ≠ LIVE TRADING
```

The graph is an in-memory typed adjacency model (`quantlab.knowledge.graph.KnowledgeGraph`) with JSON persistence beside the experiment ledger. There is no Neo4j dependency.

Desktop Knowledge Lab (`quantlab.ui.pages.knowledge_lab`) is a catalog of nodes, edges, and the last snapshot. Qt does not parse Parquet, query DuckDB, run GP, or write the ledger.

CLI: `quantlab knowledge …`. Prompt 14 keeps `quantlab research lineage` and `quantlab research replicate`.

Prompt 24 records shadow cycles, orders, fills, positions, reconciliations, incidents, and abstentions. Failed cycles are preserved. Shadow nodes are memory, not broker confirmation.
