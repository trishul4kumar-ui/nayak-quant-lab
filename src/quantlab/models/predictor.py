from typing import Protocol, runtime_checkable

from quantlab.domain.research import ModelLifecycle


@runtime_checkable
class Predictor(Protocol):
    """Fit/predict contract. A profitable backtest does not imply LIVE_APPROVED."""

    name: str
    lifecycle: ModelLifecycle

    def fit(self, features: list[list[float]], labels: list[float]) -> None: ...

    def predict(self, features: list[list[float]]) -> list[float]: ...
