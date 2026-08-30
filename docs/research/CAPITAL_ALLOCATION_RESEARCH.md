# Capital Allocation Research

Prompt 17 allocation experiments use `selection_stage = "capital_allocation"` on the existing JSONL ledger.

They may compare sizing methods, risk budgets, Kelly fractions, volatility targets, concentration limits, turnover budgets, and execution-cost assumptions. Every candidate, including infeasible and abstained runs, is recorded.

Do not treat synthetic performance as market evidence. Multiple-testing of allocation families reuses Prompt 14; Prompt 17 does not add a second FDR engine.

Related: [POSITION_SIZING.md](POSITION_SIZING.md), [KELLY_SIZING.md](KELLY_SIZING.md), [ALLOCATION_STABILITY.md](ALLOCATION_STABILITY.md).
