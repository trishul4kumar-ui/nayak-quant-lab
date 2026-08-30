# Live-trading safety gateway

**Version:** 2.6.0  
**Package:** `quantlab.safety`  
**Desktop:** Safety & Control Lab (`safety`)

This is a **safety gateway**, not a broker adapter. It answers: if an execution request were presented to the live boundary, is it authorized, valid, reconciled, risk-compliant, healthy, and safe — or must it be rejected?

`LIVE_TRADING` remains **false**. G15 Final Release always **BLOCK**. Authorization objects are not broker submits.

See [EXECUTION_AUTHORIZATION.md](EXECUTION_AUTHORIZATION.md), [SAFETY_STATE_MACHINE.md](SAFETY_STATE_MACHINE.md), [KILL_SWITCH_ARCHITECTURE.md](KILL_SWITCH_ARCHITECTURE.md), [EXECUTION_SAFETY_POLICY.md](EXECUTION_SAFETY_POLICY.md), [../research/LIVE_BOUNDARY.md](../research/LIVE_BOUNDARY.md), [../decisions/ADR-039-live-trading-safety-gateway.md](../decisions/ADR-039-live-trading-safety-gateway.md).
