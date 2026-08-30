# Execution fragility

Versioned score `fragility_v1`:

```
clip(0.4 * min(cost_stress_ratio, 1) + 0.3 * (1 - fill_ratio) + 0.3 * min(latency/5, 1), 0, 1)
```

This is a deterministic research metric, not a calibrated probability and not a confidence interval.

Monte Carlo perturbs spread/slippage; the output is a simulation distribution (`p5`…`p95`, P(net<0)), not statistical alpha significance.

CLI: `quantlab execution stress` / `quantlab research execution-fragility`.
