# Reconciliation engine

**Status:** Prompt 18 / ADR-032  
**Version:** 1.8.0

Paper OMS reconciles:

```
TargetPortfolio ↔ OrderIntent ↔ OrderPlan ↔ PaperOrder ↔ PaperFill ↔ Position ↔ Cash
```

Statuses: `RECONCILED`, `RECONCILIATION_BREAK`, `NOT_TESTED`.

Explained residuals (rounding remainder, unfilled remainder, cancelled remainder) are visible on the report and do not by themselves create a break.

Breaks (missing/duplicate/orphan fill or event, quantity mismatch, cash mismatch, unexplained target/position gap) are retained. The next successful run does not delete them.

The engine never silently repairs a discrepancy.
