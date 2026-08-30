from quantlab.core.errors import DataIntegrityError
from quantlab.core.time import PointInTime
from quantlab.domain.models import OHLCVBar


def validate_bar(bar: OHLCVBar) -> None:
    """OHLC and PIT contracts. Raises DataIntegrityError."""
    try:
        OHLCVBar.model_validate(bar.model_dump())
    except Exception as exc:  # pydantic ValidationError
        raise DataIntegrityError(str(exc)) from exc
    _validate_pit(bar.pit)


def validate_bars(bars: list[OHLCVBar]) -> list[OHLCVBar]:
    if not bars:
        raise DataIntegrityError("empty bar series")
    previous = None
    cleaned: list[OHLCVBar] = []
    for bar in bars:
        validate_bar(bar)
        t = bar.pit.event_time
        if previous is not None and t <= previous:
            raise DataIntegrityError(
                f"timestamps must increase for {bar.instrument}: {t} <= {previous}"
            )
        previous = t
        cleaned.append(bar)
    return cleaned


def _validate_pit(pit: PointInTime) -> None:
    if not pit.is_available_at(pit.available_time):
        raise DataIntegrityError("bar is not available at its own available_time")
