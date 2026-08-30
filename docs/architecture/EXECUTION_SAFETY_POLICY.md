# Execution safety policy

G0–G15 evaluate live-boundary requests. `BLOCK`, `EMERGENCY`, and critical `NOT_TESTED` prevent release. `WARN` never silently becomes authorization. `UNKNOWN → BLOCK`. Human approval cannot bypass other gates. AI may only produce `AI_SUGGESTION`.
