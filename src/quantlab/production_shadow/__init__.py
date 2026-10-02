"""Production-shadow evidence composition. Never routes orders to a broker."""

from quantlab.production_shadow.service import assess, start, stop

__all__ = ["assess", "start", "stop"]
