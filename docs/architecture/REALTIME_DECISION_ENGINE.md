# Real-Time Research-to-Decision Engine

**Version:** 3.1.0  
**Package:** `quantlab.realtime_decision`  
**Desktop:** Real-Time Decision Lab (`rt_decision`)  
**CLI:** `quantlab realtime-decision`

Decision cycle whose terminal output is `TargetPortfolio`. Not an OMS.

```text
LIVE_TRADING=false
DECISION ≠ ORDER
TARGET PORTFOLIO ≠ ORDER INTENT
```

Unknown/expired/uncertified `StrategyRelease` → ABSTAIN/BLOCK. AI cannot decide.
