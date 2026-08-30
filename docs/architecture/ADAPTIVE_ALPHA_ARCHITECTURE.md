# Adaptive alpha architecture

**Status:** Prompt 10 (2026-08-30) — ADR-024  
**Package:** `quantlab.adaptive`

An online learner may emit a research-time alpha score or ensemble weight. It may not create a broker order.

```
predict at T (state from outcomes available at T)
→ freeze prediction
→ realize label T→T+1 when that bar is available
→ score
→ update
```

Fitting on the full sample and replaying “historical predictions” is leakage unless marked retrospective.

## Policies and learners

| Seed | Policy | Learner |
|---|---|---|
| `static_mom20` | no_adaptation | Prompt 06 alpha as-is |
| `rolling_ic_mom20` | rolling_refit | emit alpha only while trailing PIT IC > 0 |
| `expanding_ic_mom20` | expanding_refit | same gate, expanding mean IC |
| `ewma_ic_mom20` | ewma_update | EWMA IC gate; `weight(age)=λ^age`, `λ=exp(-ln2/half_life)` |
| `bayes_hit_mom20` | expanding_refit | Beta(1,1) on IC>0; emit if posterior mean > 0.5 |
| `ensemble_ic_mom` | ensemble_adaptation | PIT IC-weighted mom5+mom20; hard constraints |
| `regime_vol_mom20` | regime_conditional | vol_tercile (PIT rule); smoothed HMM blocked |
| `drift_reset_mom20` | drift_triggered_refit | CUSUM on IC; reset is a research event |

Sign is not inferred from future performance. Stale-gates shrink to no-signal (empty scores), they do not flip long/short. Efficacy is the PIT IC of the underlying alpha so a silent gate can still update and later re-enter.

`adaptive/__init__.py` does not import `experiment`.

`quantlab adaptive list|inspect|run|state|decay|drift|stability|compare|prequential`
