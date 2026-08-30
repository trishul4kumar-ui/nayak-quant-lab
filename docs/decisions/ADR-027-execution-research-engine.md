# ADR-027 — Execution research engine (microstructure, costs, liquidity)

## Context
Prompt 13 asks whether an apparent statistical edge can survive spread, slippage, impact, latency, participation, and partial fills. Prompts 01–12 already own the PIT fabric, next-bar backtester, `CostSchedule`, slippage protocol, portfolio construction, firewall, ledger, and research gate. `quantlab.execution` is the OMS façade; its live path raises `SafetyError`.

## Problem
A second backtester, silent full fills, zero-cost tradability claims, or using synthetic bar volume as NSE ADV would collapse execution research into a demo.

## Options
1. Fold microstructure into `run_backtest` and replace next-bar fills
2. Add `quantlab.execution_research` as a PIT simulation layer around existing portfolio targets and the canonical backtester
3. Wire simulated fills into the OMS live path

## Decision
Option 2.

```
DATA ≠ FEATURE ≠ FACTOR ≠ ALPHA ≠ MODEL ≠ ENSEMBLE ≠ REGIME
≠ TARGET PORTFOLIO ≠ ORDER INTENT ≠ EXECUTION MODEL ≠ FILL
≠ TRANSACTION COST ≠ REALIZED P&L
```

1. Research-only simulation. A simulated fill is not a broker-confirmed fill.
2. No second backtester. Gross isolation may call `run_backtest` at 0 cost and is labelled unrealistic; net overlays decomposed execution drag.
3. Reuse Prompt 05 `CostSchedule`. Official Indian fee tables are not invented. Unspecified STT/stamp/GST/SEBI stay 0 with provenance `unspecified`.
4. PIT: `available_time <= decision_time` for price, volume, spread, liquidity, and impact inputs. Missing ≠ 0.
5. Uncalibrated impact is labelled **UNCALIBRATED**. No NSE calibration is claimed.
6. Synthetic volume is not official ADV. Capacity scenarios are inputs, not claims (`NOT_TESTED`).
7. BUY/SELL slippage and impact are adverse. Negative execution cost FAILs.
8. No fill before market arrival. Latency does not use future prices to set delay.
9. Prompt 05 remains the sole research gate. Synthetic cannot promote.
10. No brokers. `quantlab.execution` OMS is unchanged. CLI `quantlab execution` is research simulation, not live submit.
11. `LIVE_TRADING` remains false.

Desktop Execution Lab is a `quantlab.app` query viewer. It does not simulate fills.

## Consequences
- Strong gross + weak execution is WARN, not PASS.
- `exec_zero_cost` is an adversarial model that FAILs `zero_cost_execution`.
- Future volume/spread/liquidity, pre-arrival fills, hidden partials, and model mutation FAIL integrity.

## References
Prompt 13; ADR-005, ADR-019 through ADR-026
