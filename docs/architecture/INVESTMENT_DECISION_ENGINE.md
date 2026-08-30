# Investment Decision Engine

**Status:** Prompt 17 / ADR-031  
**Version:** 1.7.0

An `InvestmentDecision` is a complete deterministic capital decision at time T. After creation it is frozen. Any change creates a new decision with a new `decision_hash`.

Statuses: `REJECTED`, `ABSTAIN`, `RESEARCH_ONLY`, `ELIGIBLE`, `ALLOCATED`, `PAPER_READY`.

There is no `LIVE_READY`, `LIVE_APPROVED`, or `LIVE_ORDERED` in Prompt 17.

Synthetic data remains `RESEARCH_ONLY` at best. Prompt 05 still owns promotion. A gate `FAIL` prohibits allocation.

Decision identity includes snapshot, dataset checksum, portfolio spec, alpha/model/risk/capital policy, constraints, execution assumptions, and software version.

Abstention is first-class (`abstention_code`, `reason`, `stage`). Failed and halted decisions are retained in knowledge memory.
