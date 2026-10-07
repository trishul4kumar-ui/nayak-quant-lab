# Position review protocol

Reviews are initiated by a persisted schedule or a bounded trigger: price/stop/target
proximity, regime/factor/volatility/liquidity change, account or corporate-action event,
or human refresh. The input is frozen once and reused by both roles.

```text
fresh context + both views -> deterministic exit gate -> assessment proposal
stale context or closed position -> monitoring/reconciliation state, no ordinary proposal
```

Suggested stances are `HOLD`, `REDUCE_CANDIDATE`, `EXIT_CANDIDATE`,
`ADD_CANDIDATE`, `MORE_RESEARCH`, and `EMERGENCY_RISK_ALERT`. They are labels for
research workflows only. They never call an execution adapter.
