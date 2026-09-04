"""CLI evidence demo for auto execute, approve and edit lifecycle."""

from __future__ import annotations

import tempfile
from pathlib import Path

from audit import AuditStore
from graph import build_graph, initial_state
from hitl import approve_action, edit_action


def run_case(title: str, graph, store: AuditStore, state, thread_id: str, decision: str | None = None, payload=None) -> None:
    config = {"configurable": {"thread_id": thread_id}}
    graph.invoke(state, config)
    snapshot = graph.get_state(config)
    print(f"\n=== {title} ===")
    print(f"proposed_action={snapshot.values['proposed_action']}")
    print(f"confidence={snapshot.values['confidence_score']:.2f}")
    print(f"pending={bool(snapshot.next)} execution_status={snapshot.values.get('execution_status')}")
    if decision == "approve":
        approve_action(graph, config, "demo-reviewer")
    elif decision == "edit":
        edit_action(graph, config, "demo-reviewer", payload)
    final = graph.get_state(config).values
    print(f"decision={decision or 'auto_execute'} status={final.get('execution_status')}")
    print(f"result={final.get('execution_result')}")
    print(f"audit_records={len(store.read())}")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="day27-demo-") as directory:
        store = AuditStore(Path(directory) / "audit_log.json")
        graph = build_graph(store)
        run_case("Demo 1: low-risk high-confidence auto execute", graph, store, initial_state("demo-1", 25_000_000, 0.20), "demo-1")
        run_case("Demo 2: high-risk interrupt then approve", graph, store, initial_state("demo-2", 60_000_000, 0.90), "demo-2", "approve")
        run_case("Demo 3: low-risk low-confidence interrupt then edit", graph, store, initial_state("demo-3", 2_000_000, 0.20), "demo-3", "edit", {"template": "retention_check_in", "channel": "email", "subject": "Personalized check-in"})
        print("\nDemo completed: all three workflows used the compiled graph.")


if __name__ == "__main__":
    main()
