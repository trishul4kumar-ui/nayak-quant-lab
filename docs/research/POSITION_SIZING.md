# Position Sizing

Sizing methods in `quantlab.capital.sizing` are explicit. Each result carries `method_id`, parameters, input versions, output weights, and diagnostics.

| Method | Rule |
|---|---|
| equal_weight | `1/n` |
| score_weight | `w ∝ max(score, 0)` |
| inverse_vol | `w ∝ 1/σ` |
| risk_budget | existing ERC / custom shares |
| vol_target | score then bounded vol scale |
| fractional_kelly | constrained Kelly |
| confidence_scaled | score × allocation confidence |
| hybrid | 0.5 score + 0.5 inverse-vol |

Sharpe is not expected return. Expected return has an explicit source, horizon, and confidence. Research overrides are recorded and cannot bypass the gate.

Hard limits (position, leverage, turnover, liquidity, drawdown) always bind after sizing.
