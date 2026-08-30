# Execution authorization

Immutable hashed `ExecutionAuthorization` binds decision, target, order plan, certification, shadow/paper evidence, risk/data snapshots, account identity, policy, expiry, version, and nonce.

Any material input change invalidates the object. Minting an authorization **does not** submit a broker order. While `LIVE_TRADING=false`, `live_release` and `release_allowed` remain false.
