# Deterministic Shadow Validation, Replay & Digital Twin

**Version:** 3.1.0  
**Package:** `quantlab.digital_twin`  
**Desktop:** Digital Twin / Shadow Lab (`twin`)  
**CLI:** `quantlab twin`

Deterministic event-sourced shadow/replay. Not Prompt 24. Not a broker.

```text
LIVE_TRADING=false
BROKER_WRITE_ENABLED=false
SHADOW ≠ PAPER ≠ LIVE
DIGITAL TWIN ≠ BROKER
SIMULATED FILL ≠ BROKER CONFIRMATION
```

Write/order paths raise `TwinRoutingError`. Counterfactuals are labelled `NOT OBSERVED`.
