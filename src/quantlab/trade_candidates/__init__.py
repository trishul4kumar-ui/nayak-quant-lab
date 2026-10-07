"""Immutable, research-only candidate packets and review lifecycle."""

from quantlab.trade_candidates.builder import build_candidate
from quantlab.trade_candidates.models import TradeCandidatePacket

__all__ = ["TradeCandidatePacket", "build_candidate"]
