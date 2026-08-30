"""Production-readiness scorecard. Never collapsed into a single ready boolean."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.domain.research import CheckResult
from quantlab.shadow.enums import Score, ShadowMode
from quantlab.shadow.models import Heartbeat, ReadinessScorecard, ShadowResult
from quantlab.shadow.state import heartbeat as engine_heartbeat
from quantlab.shadow.state import last_result, mode, touch_health


def scorecard(result: ShadowResult | None = None) -> ReadinessScorecard:
    used = result or last_result()
    if used is None:
        return ReadinessScorecard(note="No shadow cycle yet. Not live.")
    cert = (
        Score.FAIL
        if used.cycle.requested_mode in {ShadowMode.PAPER, ShadowMode.SHADOW}
        and not used.cycle.production_run
        else Score.WARN
    )
    if used.cycle.production_run:
        cert = Score.PASS
    recon = Score.FAIL if used.reconciliation.breaks else Score.PASS
    data = Score.WARN
    if used.config.data_source != "synthetic_seed" and not used.freshness.stale:
        data = Score.PASS
    if used.freshness.stale:
        data = Score.FAIL
    pit = Score.PASS
    if used.integrity.checks.get("look_ahead_bias") is CheckResult.FAIL:
        pit = Score.FAIL
    return ReadinessScorecard(
        data=data,
        pit=pit,
        model=Score.WARN,
        risk=Score.WARN,
        capital=Score.WARN,
        execution=Score.WARN if used.orders else Score.NOT_TESTED,
        reconciliation=recon,
        monitoring=Score.NOT_TESTED,
        tca=Score.NOT_TESTED,
        certification=cert,
        safety=Score.PASS if not used.live_trading else Score.FAIL,
        recovery=Score.WARN if used.checkpoint else Score.NOT_TESTED,
        observability=Score.WARN,
        note=(
            "Diagnostic scorecard. Synthetic remains WARN. "
            "Do not collapse into a ready boolean. Not live."
        ),
    )


def heartbeat() -> Heartbeat:
    touch_health(datetime.now(tz=UTC).isoformat())
    beat = engine_heartbeat()
    current = mode()
    idle = current in {ShadowMode.OFF, ShadowMode.PAUSED} and last_result() is not None
    return beat.model_copy(update={"idle": idle, "dead": False})
