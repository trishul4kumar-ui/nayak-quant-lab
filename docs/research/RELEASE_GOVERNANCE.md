# Release Governance

An immutable `ReleaseManifest` binds software, configuration, research/data/model hashes, policies, capital limit, expiry, approver, and validator.

Material mutation invalidates certification. Expired, suspended, and revoked certifications cannot become live — live is not a state in this engine. CLI: `quantlab certification status|audit|manifest`.
