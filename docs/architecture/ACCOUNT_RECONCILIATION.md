# Account Reconciliation

Three-way reconciliation:

```text
BROKER STATE ↔ GATEWAY SNAPSHOT ↔ QUANT LAB INTERNAL STATE
```

Results: `RECONCILED | PARTIAL | MISMATCH | RECONCILIATION_REQUIRED | BLOCKED`.

Unknown broker orders and orphan fills are first-class and never silently repaired. Ambiguous instrument mappings fail closed. Duplicate external events with the same identity and payload are idempotent; the same identity with a different payload is an integrity failure.
