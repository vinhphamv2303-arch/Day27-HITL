"""Shared typed state and validated audit schema."""

from __future__ import annotations

from typing import Any, TypedDict

from pydantic import BaseModel, Field


class GraphState(TypedDict, total=False):
    """State persisted by LangGraph across an interrupt and resume."""

    customer_id: str
    total_operating_income: float
    churn_probability: float
    proposed_action: str
    confidence_score: float
    reasoning: str
    human_decision: str | None
    action_payload: dict[str, Any]
    edited_action_payload: dict[str, Any] | None
    reviewer_id: str | None
    route: str | None
    execution_status: str | None
    execution_result: str | None


class AuditEntry(BaseModel):
    """One immutable event in the lab audit trail."""

    timestamp: str = Field(min_length=1)
    agent_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    reviewer_id: str = Field(min_length=1)
    decision: str = Field(min_length=1)
    customer_id: str | None = None
    original_action: str | None = None
    final_action: str | None = None
    execution_status: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
