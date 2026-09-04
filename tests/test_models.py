import pytest
from pydantic import ValidationError

from models import AuditEntry, GraphState


def test_graph_state_has_required_fields():
    state: GraphState = {
        "customer_id": "c-1",
        "proposed_action": "send_email",
        "confidence_score": 0.9,
        "reasoning": "data-based",
        "human_decision": None,
    }
    assert state["customer_id"] == "c-1"


def test_audit_entry_schema_and_confidence_validation():
    entry = AuditEntry(timestamp="2026-01-01T00:00:00+00:00", agent_id="agent", action="send_email", confidence=0.9, reviewer_id="system-policy", decision="auto_execute")
    assert entry.confidence == 0.9
    with pytest.raises(ValidationError):
        AuditEntry(timestamp="t", agent_id="a", action="x", confidence=1.1, reviewer_id="r", decision="d")
    with pytest.raises(ValidationError):
        AuditEntry(timestamp="t", agent_id="a", action="x", confidence=0.5, reviewer_id="", decision="d")
