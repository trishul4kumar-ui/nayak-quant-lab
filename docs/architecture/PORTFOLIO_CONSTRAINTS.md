# Portfolio constraints

**Status:** Prompt 08 (2026-08-30) — ADR-022 extends ADR-021; missing beta is not zero  
**Package:** `quantlab.portfolio.constraints`

Hard constraints cannot be silently relaxed. Soft constraints emit warnings only.

| Kind | Default seed (long-only) |
|---|---|
| `long_only` | hard |
| `sum_to_one` | hard, sum ≤ 1 (cash remainder allowed) |
| `max_weight` | hard, 0.5 (omitted for unconstrained min-var seed) |
| `max_gross` | hard, 1.0 |
| `max_turnover` | optional; two-sided `0.5 × Σ\|Δw\|` |
| `max_beta` | opt-in; unknown beta is infeasible, not assumed zero |
| `max_factor_exposure` | opt-in; requires `tag`; missing exposure is infeasible |

`InfeasiblePortfolio` is a valid research result. There is no secret clip-to-fit inside the constructor. The risk firewall still runs on the existing authorize path; research experiments set name caps so the firewall does not secretly tighten the documented constraint set.

Turnover convention matches the next-bar engine: `0.5 * L1`.
