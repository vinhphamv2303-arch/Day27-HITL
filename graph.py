"""LangGraph churn-risk workflow with a real interrupt-before checkpoint."""

from __future__ import annotations

import json
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from audit import AuditStore, append_audit, utc_timestamp
from models import GraphState


CONFIDENCE_THRESHOLD = 0.85
HIGH_RISK_ACTION = "increase_credit_limit"
LOW_RISK_ACTION = "send_email"


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def evaluate_customer(state: GraphState) -> dict[str, Any]:
    """Produce a reproducible proposal from customer data, without an LLM."""

    income = max(0.0, float(state.get("total_operating_income", 0.0)))
    churn = _bounded(float(state.get("churn_probability", 0.0)))

    if churn >= 0.65:
        action = HIGH_RISK_ACTION
        confidence = min(0.96, 0.78 + (churn - 0.65) * 0.5)
        payload = {"amount": 50_000_000, "currency": "VND"}
        reasoning = (
            f"Churn probability is {churn:.0%}, so a retention credit-limit proposal "
            f"was generated for income {income:,.0f} VND. This action is policy-sensitive."
        )
    else:
        action = LOW_RISK_ACTION
        confidence = 0.90 if income >= 10_000_000 else 0.82
        payload = {"template": "retention_check_in", "channel": "email"}
        reasoning = (
            f"Churn probability is {churn:.0%}; a low-risk retention email is suitable. "
            f"Income context: {income:,.0f} VND."
        )

    return {
        "proposed_action": action,
        "confidence_score": _bounded(confidence),
        "reasoning": reasoning,
        "action_payload": payload,
        "edited_action_payload": None,
        "human_decision": None,
        "reviewer_id": None,
        "execution_status": None,
        "execution_result": None,
    }


def route_action(state: GraphState) -> str:
    """Apply policy first, then confidence routing."""

    action = state["proposed_action"]
    confidence = float(state["confidence_score"])
    if action == HIGH_RISK_ACTION:
        return "execute_high_risk_action"
    if confidence >= CONFIDENCE_THRESHOLD:
        return "execute_low_risk_action"
    return "execute_high_risk_action"


def _audit_fields(state: GraphState, *, decision: str, status: str, final_action: str | None = None) -> dict[str, Any]:
    final_payload = state.get("edited_action_payload") if decision == "edit" else state.get("action_payload")
    return {
        "timestamp": utc_timestamp(),
        "agent_id": "local-churn-agent",
        "action": state["proposed_action"],
        "confidence": float(state["confidence_score"]),
        "reviewer_id": state.get("reviewer_id") or "system-policy",
        "decision": decision,
        "customer_id": state.get("customer_id"),
        "original_action": state["proposed_action"],
        "final_action": final_action or state["proposed_action"],
        "execution_status": status,
        "metadata": {
            "original_payload": state.get("action_payload", {}),
            "final_payload": final_payload or {},
        },
    }


def execute_low_risk_action(state: GraphState, *, audit_store: AuditStore | None = None) -> dict[str, str]:
    """Simulate a safe action immediately and write a traceable audit event."""

    if audit_store is not None:
        append_audit(audit_store, **_audit_fields(state, decision="auto_execute", status="executed"))
    return {
        "execution_status": "executed",
        "execution_result": f"Simulated {state['proposed_action']} successfully (no external message sent).",
    }


def execute_high_risk_action(state: GraphState, *, audit_store: AuditStore | None = None) -> dict[str, str]:
    """Execute, reject, or apply an edited payload after the HITL decision."""

    decision = state.get("human_decision")
    if decision == "reject":
        status = "rejected"
        result = "Action rejected by human reviewer; nothing was executed."
        final_action = state["proposed_action"]
    elif decision in {"approve", "edit"}:
        payload = state.get("edited_action_payload") if decision == "edit" else state.get("action_payload")
        status = "executed"
        final_action = state["proposed_action"]
        result = f"Simulated {final_action} with payload {json.dumps(payload, sort_keys=True)}; no external side effect performed."
    else:
        raise ValueError("High-risk action can only resume with approve, reject, or edit")

    if audit_store is not None:
        append_audit(audit_store, **_audit_fields(state, decision=decision, status=status, final_action=final_action))
    return {"execution_status": status, "execution_result": result}


def build_graph(audit_store: AuditStore | None = None):
    """Build one compiled graph/checkpointer pair for an app or test session."""

    store = audit_store or AuditStore()
    builder = StateGraph(GraphState)
    builder.add_node("evaluate_customer", evaluate_customer)
    builder.add_node("execute_low_risk_action", lambda state: execute_low_risk_action(state, audit_store=store))
    builder.add_node("execute_high_risk_action", lambda state: execute_high_risk_action(state, audit_store=store))
    builder.add_edge(START, "evaluate_customer")
    builder.add_conditional_edges(
        "evaluate_customer",
        route_action,
        {
            "execute_low_risk_action": "execute_low_risk_action",
            "execute_high_risk_action": "execute_high_risk_action",
        },
    )
    builder.add_edge("execute_low_risk_action", END)
    builder.add_edge("execute_high_risk_action", END)
    memory = MemorySaver()
    return builder.compile(checkpointer=memory, interrupt_before=["execute_high_risk_action"])


def initial_state(customer_id: str, total_operating_income: float, churn_probability: float) -> GraphState:
    return {
        "customer_id": customer_id,
        "total_operating_income": float(total_operating_income),
        "churn_probability": float(churn_probability),
        "proposed_action": "",
        "confidence_score": 0.0,
        "reasoning": "",
        "human_decision": None,
        "action_payload": {},
        "edited_action_payload": None,
        "reviewer_id": None,
        "route": None,
        "execution_status": None,
        "execution_result": None,
    }
