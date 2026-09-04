from graph import initial_state
from tests.helpers import config


def test_low_risk_high_confidence_completes_and_audits(workflow):
    graph, store = workflow
    thread = config("lifecycle-auto")
    graph.invoke(initial_state("customer-auto", 25_000_000, 0.20), thread)
    snapshot = graph.get_state(thread)
    assert snapshot.next == ()
    assert snapshot.values["execution_status"] == "executed"
    assert store.read()[-1]["decision"] == "auto_execute"


def test_low_risk_low_confidence_interrupts_before_execution(workflow):
    graph, store = workflow
    thread = config("lifecycle-review")
    graph.invoke(initial_state("customer-review", 2_000_000, 0.20), thread)
    snapshot = graph.get_state(thread)
    assert "execute_high_risk_action" in snapshot.next
    assert snapshot.values["proposed_action"] == "send_email"
    assert snapshot.values.get("execution_status") is None
    assert store.read() == []
