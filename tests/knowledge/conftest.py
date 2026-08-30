from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolate_knowledge(tmp_path, monkeypatch):
    from quantlab.knowledge import memory

    memory._PROCESS = None
    monkeypatch.setattr(memory, "default_path", lambda: tmp_path / "knowledge.json")
    yield
    memory._PROCESS = None
