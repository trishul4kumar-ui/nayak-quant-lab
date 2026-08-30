"""Knowledge-graph ingest for shadow events. Failed cycles are preserved."""

from __future__ import annotations

from pathlib import Path

from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.ingest import ingest_shadow as _ingest
from quantlab.knowledge.ingest import persist_shadow as _persist
from quantlab.shadow.models import ShadowResult


def ingest_shadow(graph: KnowledgeGraph, result: ShadowResult) -> None:
    _ingest(graph, result)


def persist_shadow(result: ShadowResult, ledger_path: Path) -> None:
    _persist(result, ledger_path)
