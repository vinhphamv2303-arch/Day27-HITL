from pathlib import Path

import pytest

from audit import AuditStore
from graph import build_graph


@pytest.fixture
def workflow(tmp_path: Path):
    store = AuditStore(tmp_path / "audit_log.json")
    return build_graph(store), store


def config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}
