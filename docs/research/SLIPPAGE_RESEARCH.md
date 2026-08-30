# Slippage research

Configured models: none, fixed bps, spread fraction, vol-scaled, volume-scaled.

Directionality: BUY execution price must not improve; SELL execution price must not improve. Wrong-side slippage FAILs integrity.

`none` is optimistic (WARN). Volume-scaled slippage is not broker TCA.

CLI: `quantlab execution slippage`.
