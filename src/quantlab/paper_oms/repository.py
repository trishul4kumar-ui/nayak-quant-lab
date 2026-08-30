"""JSON persistence for paper OMS. Reuses project conventions; not a second ledger."""

from pathlib import Path

from quantlab.paper_oms.state import default_path, load, persist

__all__ = ["default_path", "load", "persist"]


def save(path: Path | None = None) -> None:
    persist(path)


def restore(path: Path | None = None) -> None:
    load(path)
