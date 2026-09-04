"""Framework-independent human decision service for the HITL workflow."""

from __future__ import annotations

from typing import Any


VALID_DECISIONS = {"approve", "reject", "edit"}


def pending_state(graph: Any, config: dict[str, Any]) -> dict[str, Any]:
    snapshot = graph.get_state(config)
    if not snapshot.next or "execute_high_risk_action" not in snapshot.next:
        raise ValueError("Workflow is not pending human review")
    return dict(snapshot.values)


def submit_human_decision(
    graph: Any,
    config: dict[str, Any],
    decision: str,
    reviewer_id: str,
    edited_payload: dict[str, Any] | None = None,
):
    """Validate, persist and resume a pending workflow on its original thread."""

    if decision not in VALID_DECISIONS:
        raise ValueError(f"decision must be one of {sorted(VALID_DECISIONS)}")
    if not reviewer_id or not reviewer_id.strip():
        raise ValueError("reviewer_id is required")
    pending_state(graph, config)
    if decision == "edit":
        if not isinstance(edited_payload, dict) or not edited_payload:
            raise ValueError("edited_payload is required for edit")
        update = {"human_decision": decision, "reviewer_id": reviewer_id, "edited_action_payload": edited_payload}
    else:
        update = {"human_decision": decision, "reviewer_id": reviewer_id}
    graph.update_state(config, update)
    graph.invoke(None, config)
    return graph.get_state(config)


def approve_action(graph: Any, config: dict[str, Any], reviewer_id: str):
    return submit_human_decision(graph, config, "approve", reviewer_id)


def reject_action(graph: Any, config: dict[str, Any], reviewer_id: str):
    return submit_human_decision(graph, config, "reject", reviewer_id)


def edit_action(graph: Any, config: dict[str, Any], reviewer_id: str, edited_payload: dict[str, Any]):
    return submit_human_decision(graph, config, "edit", reviewer_id, edited_payload)
