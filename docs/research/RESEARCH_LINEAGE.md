# Research lineage

The control-plane graph is:

```
Hypothesis → Family → Candidates (models / portfolios / execution / falsifiers)
```

Deleting a parent is a lineage break. Ledger rows use `parent_experiment_id` and `orchestration_id`. There is no second ledger.

CLI: `quantlab research lineage EXP-MOM-001`.
