# Secrets management

Provider-neutral `SecretReference` / metadata / access audit. Values never appear in logs, CLI, UI, ledger, or exceptions. Ambiguous live credential env vars (`BROKER_PASSWORD`, Kite/Zerodha/OpenAlgo tokens) are rejected. Expired secrets fail closed.
