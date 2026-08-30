from quantlab.data.fabric.features import FeatureStatus, momentum_spec


def test_momentum_lookback_is_trading_sessions() -> None:
    spec = momentum_spec(20, calendar_version="weekday-v1")
    assert spec.lookback_sessions == 20
    assert spec.status(20) is FeatureStatus.INSUFFICIENT_HISTORY
    assert spec.status(21) is FeatureStatus.READY
