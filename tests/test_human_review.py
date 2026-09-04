from graph import initial_state
from hitl import approve_action, edit_action, reject_action

from tests.helpers import config


def start_pending(graph, thread):
    graph.invoke(initial_state(thread, 60_000_000, 0.9), config(thread))
    return config(thread)


def test_approve_resumes_and_audits(workflow):
    graph, store = workflow
    thread = start_pending(graph, "approve-1")
    snapshot = approve_action(graph, thread, "reviewer-a")
    assert snapshot.values["execution_status"] == "executed"
    assert snapshot.values["reviewer_id"] == "reviewer-a"
    assert store.read()[-1]["decision"] == "approve"


def test_reject_aborts_without_execution(workflow):
    graph, store = workflow
    thread = start_pending(graph, "reject-1")
    snapshot = reject_action(graph, thread, "reviewer-r")
    assert snapshot.values["execution_status"] == "rejected"
    assert "nothing was executed" in snapshot.values["execution_result"]
    assert store.read()[-1]["decision"] == "reject"


def test_edit_executes_edited_payload_and_audits_final_value(workflow):
    graph, store = workflow
    thread = start_pending(graph, "edit-1")
    snapshot = edit_action(graph, thread, "reviewer-e", {"amount": 20_000_000, "currency": "VND"})
    assert snapshot.values["execution_status"] == "executed"
    assert "20000000" in snapshot.values["execution_result"]
    assert "50000000" not in snapshot.values["execution_result"]
    record = store.read()[-1]
    assert record["decision"] == "edit"
    assert record["final_action"] == "increase_credit_limit"
    assert record["metadata"]["original_payload"]["amount"] == 50_000_000
    assert record["metadata"]["final_payload"]["amount"] == 20_000_000
