# Reproducibility

**Version:** 2.3.0

`validation_replay` recomputes the candidate+checklist hash and compares it to the frozen `evidence_hash`. Any unexplained difference is `ReproductionBreak` and blocks certification. Environment metadata is recorded; it is not a substitute for hash equality.
