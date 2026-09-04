from graph import initial_state

from tests.helpers import config


def test_high_risk_interrupt_preserves_state_and_does_not_execute(workflow):
    graph, store = workflow
    thread = config("interrupt-1")
    graph.invoke(initial_state("customer-1", 60_000_000, 0.9), thread)
    snapshot = graph.get_state(thread)
    assert "execute_high_risk_action" in snapshot.next
    assert snapshot.values["customer_id"] == "customer-1"
    assert snapshot.values["proposed_action"] == "increase_credit_limit"
    assert snapshot.values["confidence_score"] >= 0.0
    assert snapshot.values["reasoning"]
    assert snapshot.values.get("execution_status") is None
    assert store.read() == []


def test_new_thread_does_not_see_pending_workflow(workflow):
    graph, _ = workflow
    graph.invoke(initial_state("customer-2", 60_000_000, 0.9), config("original"))
    fresh = graph.get_state(config("different"))
    assert fresh.values == {}
    assert fresh.next == ()
