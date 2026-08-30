# Execution

OMS state machine lives in `quantlab.execution`. Live path raises SafetyError until Phase 10.

Research simulation of spread, slippage, impact, latency, and participation lives in `quantlab.execution_research` (Prompt 13 / ADR-027). Simulated fills are not broker fills and never call `ExecutionEngine.submit`.
