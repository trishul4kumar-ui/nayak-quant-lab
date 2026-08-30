# Evidence provenance

Every assertion traces to an experiment, dataset snapshot, config hash, integrity status, and gate outcome. `EvidenceRecord` is append-only. AI-generated text is labeled (`AI_GENERATED_*`) and cannot be stored as empirical evidence (`ai_evidence_confusion`).

Synthetic evidence may be `PRELIMINARY` / `WARN`. It cannot become `VALIDATED` or `REPLICATED` market knowledge (`synthetic_evidence_overpromotion`). Prompt 05 remains the only promotion gate.
