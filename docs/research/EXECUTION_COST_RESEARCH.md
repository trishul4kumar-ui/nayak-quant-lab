# Execution cost research

Decompose simulated drag:

```
total = spread + slippage + impact + explicit
```

Explicit legs come from Prompt 05 `CostSchedule` (default 10 bps commission). STT, stamp, GST, and SEBI are **unspecified at 0** — not an official India fee table.

Gross edge isolation may run the canonical next-bar engine at zero cost. That path is labelled unrealistic. Net edge = gross − cost/capital.

Zero-cost execution FAILs integrity (`zero_cost_execution`) and cannot be treated as tradability evidence.

CLI: `quantlab execution costs` / `quantlab research execution-cost`.
