# Ensemble stability

Weight variance, turnover (`0.5 × L1(w_t − w_{t-1})`), sign/rank stability, and maximum weight change are research diagnostics.

High gross IC caused by weight churn must be visible. Flags such as `high_weight_turnover` and `weight_concentration` are warnings, not live-trading permissions.

Historical scores and weights at T must not change when future bars are appended (`model_state_mutation` otherwise).

`quantlab ensemble stability roll_ic_mom`  
`quantlab research ensemble-stability`
