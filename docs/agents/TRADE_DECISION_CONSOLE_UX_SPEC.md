# Trade Decision Console UX contract

The console has three canonical read-only tabs:

1. **Levels / Chart** — deterministic entry zone, invalidation, stop, targets,
   trailing/time logic, and exit policy. It does not fabricate candles.
2. **Research / Analytics** — distinct raw Bull/Bear confidence, calibration status,
   evidence, hard blockers, and not-tested fields.
3. **Provenance / Audit** — candidate and upstream artifact hashes.

Freshness is evaluated before paper approval. A review action records human intent;
it does not mutate a position, stage an order, or bypass any later authorization gate.
