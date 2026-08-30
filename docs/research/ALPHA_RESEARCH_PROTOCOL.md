# Alpha research protocol

1. Bind an `AlphaDefinition` to a hypothesis and named input features.
2. Apply an explicit transformation (rank, z-score, weighted z-score, rank average, linear combo). Weights are not fit on the test set.
3. Run the feature pipeline on the combined panel.
4. Optional portfolio bridge: map the panel to `Signal` objects and the existing genome/backtest path.
5. Economic claims require Prompt 05 validation (`quantlab validate run`) on the same next-bar, 10 bps engine.
6. Synthetic results stay at gate `WARN`. They cannot be paper or live.

`quantlab alpha list|inspect`  
`quantlab research alpha <id>`  
`quantlab research ensemble <id>`  
`quantlab research portfolio <id>`  
`quantlab portfolio list|inspect|build`
