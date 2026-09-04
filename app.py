"""Streamlit UI for the local LangGraph HITL demo."""

from __future__ import annotations

import uuid

import streamlit as st

from audit import AuditStore
from graph import build_graph, initial_state
from hitl import approve_action, edit_action, pending_state, reject_action


def get_app_graph():
    if "workflow_graph" not in st.session_state:
        st.session_state.audit_store = AuditStore()
        st.session_state.workflow_graph = build_graph(st.session_state.audit_store)
    return st.session_state.workflow_graph


def main() -> None:
    st.set_page_config(page_title="Day27 HITL", page_icon="🧭", layout="centered")
    st.title("Day27 — Churn Risk HITL")
    st.caption("Local deterministic reasoning · policy threshold: 0.85")
    graph = get_app_graph()

    with st.form("evaluate"):
        customer_id = st.text_input("Customer ID", value="customer-demo")
        income = st.number_input("Total Operating Income", min_value=0.0, value=25_000_000.0, step=1_000_000.0)
        churn = st.slider("Churn Probability", 0.0, 1.0, 0.20, 0.01)
        evaluate = st.form_submit_button("Evaluate Customer", type="primary")
    if evaluate:
        thread_id = f"streamlit-{uuid.uuid4()}"
        st.session_state.thread_id = thread_id
        graph.invoke(initial_state(customer_id, income, churn), {"configurable": {"thread_id": thread_id}})
        st.rerun()

    thread_id = st.session_state.get("thread_id")
    if thread_id:
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = graph.get_state(config)
        values = snapshot.values
        if values.get("execution_status"):
            st.subheader("Workflow result")
            route_label = "auto execute" if values.get("route") == "execute_low_risk_action" else "human review"
            st.write(f"Route: **{route_label}**")
            st.write(f"Proposed action: `{values.get('proposed_action')}`")
            st.write(f"Confidence: `{values.get('confidence_score', 0):.2f}`")
            st.info(values.get("reasoning", ""))
            st.success(f"{values['execution_status']}: {values.get('execution_result', '')}")
        elif snapshot.next:
            values = pending_state(graph, config)
            st.subheader("Human Review")
            st.write(f"Customer ID: `{values.get('customer_id')}`")
            st.write(f"Proposed Action: `{values.get('proposed_action')}`")
            st.json(values.get("action_payload", {}))
            st.write(f"Confidence Score: `{values.get('confidence_score', 0):.2f}`")
            st.write(f"Reasoning: {values.get('reasoning', '')}")
            st.warning("Review required because the action is policy-sensitive or confidence is below 0.85.")
            reviewer_id = st.text_input("Reviewer ID", key="reviewer_id")
            edit_amount = None
            if values.get("proposed_action") == "increase_credit_limit":
                original_amount = values.get("action_payload", {}).get("amount", 0)
                edit_amount = st.number_input("Edited credit amount (VND)", min_value=0.0, value=float(original_amount), step=1_000_000.0)
            col1, col2, col3 = st.columns(3)
            if col1.button("Approve", disabled=not reviewer_id):
                approve_action(graph, config, reviewer_id)
                st.rerun()
            if col2.button("Reject", disabled=not reviewer_id):
                reject_action(graph, config, reviewer_id)
                st.rerun()
            if col3.button("Edit", disabled=not reviewer_id):
                payload = dict(values.get("action_payload", {}))
                if edit_amount is not None:
                    payload["amount"] = edit_amount
                edit_action(graph, config, reviewer_id, payload)
                st.rerun()

    st.subheader("Audit Trail")
    records = st.session_state.audit_store.read()
    if records:
        fields = ["timestamp", "customer_id", "action", "confidence", "reviewer_id", "decision", "execution_status"]
        st.dataframe([{key: row.get(key) for key in fields} for row in records[-20:]], use_container_width=True, hide_index=True)
    else:
        st.caption("No audit records yet.")


if __name__ == "__main__":
    main()
