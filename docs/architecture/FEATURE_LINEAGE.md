# Feature lineage

Every feature experiment records:

- `feature_id` / `feature_version` / `feature_identity_hash`
- `dataset_id`, `dataset_version`, `snapshot_id`, checksum
- operator and implementation version
- universe, time range, frequency, normalization
- label id and horizon
- `research_family_id`, `n_hypotheses_in_family`, `selection_stage`
- integrity map and gate outcome

Cache keys include snapshot, feature identity, operator version, universe, range, frequency, and normalization. A mismatch is a miss.

Artifacts are written under `RuntimePaths.artifacts_dir / experiment_id` (config, feature_definition, label_definition, feature_quality, ic, quantiles, decay, correlations, validation, integrity, lineage). The JSONL ledger is append-only; failed experiments are not deleted.

If an AI agent later proposes a feature, record `proposal_id`, agent, timestamp, definition, and parent hypothesis. There is no `predict_stock()` or `ai_alpha()`.
