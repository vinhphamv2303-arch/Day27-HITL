from audit import AuditStore, append_audit
from models import AuditEntry


def make_entry(decision: str) -> AuditEntry:
    return AuditEntry(timestamp=f"2026-01-01T00:00:0{len(decision)}+00:00", agent_id="agent", action="send_email", confidence=0.9, reviewer_id="reviewer", decision=decision)


def test_audit_append_preserves_history(tmp_path):
    store = AuditStore(tmp_path / "audit_log.json")
    append_audit(store, **make_entry("first").model_dump())
    append_audit(store, **make_entry("second").model_dump())
    records = store.read()
    assert len(records) == 2
    assert [row["decision"] for row in records] == ["first", "second"]
