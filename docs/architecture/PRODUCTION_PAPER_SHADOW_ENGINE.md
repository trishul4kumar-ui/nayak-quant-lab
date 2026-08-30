# Production Paper / Shadow Engine

**Version:** 2.4.0  
**Package:** `quantlab.shadow`  
**CLI:** `quantlab shadow`  
**Desktop:** Shadow Trading Lab (`shadow`)

Prompt 24 composes existing engines into a production-like paper and shadow loop. It is not a second backtester, paper OMS, data fabric, risk engine, or TCA engine.

```
LIVE_TRADING = FALSE
SHADOW EXECUTION ≠ PAPER OMS ≠ BROKER EXECUTION
```

Seed cycles use the Prompt 18 synthetic AAA/BBB/CCC snapshot and are labelled `RESEARCH_PAPER`. They are architecture diagnostics, not market evidence.

Qt queries `quantlab.app.shadow` only. The empty action is **RUN SHADOW**. There is no live-order control.
