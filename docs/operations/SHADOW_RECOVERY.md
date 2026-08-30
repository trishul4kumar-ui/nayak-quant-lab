# Shadow Recovery

**Version:** 2.4.0

Restart path: LOAD checkpoint → VERIFY HASH → RECONCILE → FRESHNESS → RESUME or ABSTAIN.

```bash
quantlab shadow checkpoint
quantlab shadow recover
```

Corrupt checkpoints fail closed (`CheckpointError`). Recovery without reconciliation is FAIL. After a recon break the engine HALTs; it does not invent fills to make the books match.
