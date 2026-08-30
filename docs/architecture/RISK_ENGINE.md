# Research risk engine

**Status:** Prompt 08 (2026-08-30) — ADR-022  
**Package:** `quantlab.risk` (research modules) — **not** the live firewall

The live `RiskFirewall` remains the only authorization path. `risk/__init__.py` still exports only `RiskFirewall`, `RiskLimits`, and `RiskState`.

Research risk lives beside it:

| Module | Role |
|---|---|
| `risk.model` | Versioned covariance + factor-set spec |
| `portfolio.covariance` | Sample / EWMA / diagonal-shrinkage Σ(T) |
| `risk.regression` | OLS, VIF, condition number |
| `risk.decomposition` | Factor vs idiosyncratic when B and Ω exist |
| `risk.stress` | Explicit scenarios; **not forecasts** |
| `risk.experiment` | Ledger + Prompt 05 gate |

A risk estimate describes variance and exposure. It does not invent expected return. Prompt 08 must not turn this package into the Prompt 07 optimizer.

`risk.experiment` may import `portfolio.covariance` and `factors`. Construction/builder must not import `risk.experiment`.

Desktop Risk Lab is a `quantlab.app` query viewer. The UI does not compute covariance or weights.
