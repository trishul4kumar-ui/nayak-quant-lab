# Alpha decay

Two different decay objects exist:

| Object | Package | Question |
|---|---|---|
| Predictive horizon decay | `quantlab.alpha.decay` | IC vs forward return at horizon H |
| Efficacy half-life | `quantlab.adaptive.decay` | How fast realized IC fades over calendar time |

Half-life is estimated with OLS of IC on session index. If intercept ≤ 0 or slope ≥ 0, status is `UNSTABLE` and no number is invented. Short samples are `INSUFFICIENT_DATA`. Low R² is `UNSTABLE` even if a point estimate exists.

A half-life is not a forecast that the alpha will die on that date. Regime-conditioned half-lives require PIT regime labels (Prompt 09 filtered/rule). Smoothed labels are blocked.

`quantlab adaptive decay <alpha>`  
`quantlab research alpha-decay <alpha>`
