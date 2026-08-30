"""Shared copy for honest synthetic-data labeling."""

SYNTHETIC_SHARPE_DISCLAIMER = (
    "Synthetic drift data — Sharpe here teaches mechanics, not NIFTY edge."
)


def format_sharpe(sharpe: float | None) -> str:
    if sharpe is None:
        return "n/a"
    return f"{sharpe:.2f}"


def sharpe_with_context(sharpe: float | None, *, data_kind: str = "synthetic") -> str:
    text = format_sharpe(sharpe)
    if data_kind == "synthetic":
        return f"{text} ({SYNTHETIC_SHARPE_DISCLAIMER})"
    return text
