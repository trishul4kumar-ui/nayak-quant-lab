"""Canonical JSON for graph hashes. No volatile UI state."""

from __future__ import annotations

import json
from pathlib import Path

from quantlab.knowledge.graph import KnowledgeGraph


def dump_graph(graph: KnowledgeGraph) -> str:
    payload = graph.model_dump(mode="json")
    return json.dumps(payload, sort_keys=True, default=str, indent=2) + "\n"


def save_graph(graph: KnowledgeGraph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_graph(graph), encoding="utf-8")


def load_graph(path: Path) -> KnowledgeGraph:
    return KnowledgeGraph.model_validate_json(path.read_text(encoding="utf-8"))
