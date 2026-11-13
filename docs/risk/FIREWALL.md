# Risk

The firewall is mandatory. See ADR-006 and `quantlab.risk.firewall.RiskFirewall`.

The firewall rejects duplicate instruments, excess position counts and non-finite
weights. Per-name clipping applies symmetrically to permitted long and short
positions; gross exposure is checked after clipping. Limits must be finite and
non-negative. These checks protect the existing portfolio authorization boundary;
they do not supply loss, drawdown, sector, liquidity or independently sourced
point-in-time evidence, and do not authorize broker execution.

The existing capital drawdown classifier also halts on non-finite drawdown or
invalid threshold policy. This does not establish that a drawdown input was
observed, independently reconciled, or sufficiently fresh for capital decisions.

The firewall additionally supports an **opt-in** daily-loss guard. Its owner must
explicitly supply a loss threshold, maximum observation age and market timezone.
Every guarded authorization requires cash-flow-adjusted opening/current equity,
the market session date, observation and availability timestamps, a source and a
source checksum. Missing, future, stale, cross-session, non-finite, malformed or
over-limit evidence rejects the portfolio. The evidence is caller-supplied: these
checks do not independently verify the checksum, equity, session calendar, cash
flows, account reconciliation or the source's licence. No broker source, live
configuration, market limit or automatic session reset is introduced here. Existing
callers remain unguarded unless they explicitly configure the policy and provide
evidence on each authorization.

Capital allocation treats a missing or inconsistent research gate as research-only
(or rejects it when the configured policy requires a gate). Unknown data kinds are
rejected. A gate marked paper-promoted is not itself a separate paper authorization.
Non-finite or non-positive ADV and invalid participation limits are unknown, never
infinite liquidity. A permissive unknown-liquidity policy cannot elevate the
result above research-only. These checks do not provide time-stamped, independently
verified ADV history or a live risk certification.
