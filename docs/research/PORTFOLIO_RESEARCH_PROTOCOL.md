# Portfolio research protocol

1. Bind a versioned `AlphaEnsemble` (explicit component weights; no test-set search).
2. Choose a `PortfolioModel` constructor. Start with top-N / equal-weight / rank-weight before min-var or ERC.
3. Pin Universe(T), missing-alpha policy, rebalance, cost_bps (default 10), and constraint hardness.
4. Build target weights from scores available at T. Covariance, if used, is PIT sample cov through T.
5. Run the **existing** next-bar engine (`WeightMapStrategy` → firewall → `run_backtest`).
6. Record integrity, Prompt 05 gate, ledger row, artifacts. Do not delete a failed or infeasible run.
7. Synthetic `data_kind` stays at gate `WARN`. It cannot be paper or live.

`quantlab portfolio list|inspect|build|risk|exposures|turnover|compare`  
`quantlab research ensemble <id> | portfolio <id> | alpha-correlation`
