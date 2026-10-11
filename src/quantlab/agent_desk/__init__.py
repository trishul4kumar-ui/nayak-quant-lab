"""Persistent, bounded research-desk orchestration. Never an execution service."""

from quantlab.agent_desk.service import DailyDeskService
from quantlab.agent_desk.supervisor import route_research_job

__all__ = ["DailyDeskService", "route_research_job"]
