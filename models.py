"""Shared typed state and validated audit schema."""

from __future__ import annotations

from typing import Any, NotRequired, Required, TypedDict

from pydantic import BaseModel, Field


class GraphState(TypedDict, total=False):
    """State persisted by LangGraph across an interrupt and resume."""

    customer_id: Required[str]
    proposed_action: Required[str]
    confidence_score: Required[float]
    reasoning: Required[str]
    human_decision: Required[str | None]
    total_operating_income: NotRequired[float]
    churn_probability: NotRequired[float]
    action_payload: NotRequired[dict[str, Any]]
    edited_action_payload: NotRequired[dict[str, Any] | None]
    reviewer_id: NotRequired[str | None]
    route: NotRequired[str | None]
    execution_status: NotRequired[str | None]
    execution_result: NotRequired[str | None]


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
