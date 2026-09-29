from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=80)
    user_id: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=4000)
    permissions: set[str] = Field(default_factory=set)


class Citation(BaseModel):
    source: str
    excerpt: str


class TraceStep(BaseModel):
    stage: str
    status: Literal["ok", "blocked", "error"]
    detail: str
    duration_ms: float = 0


class AgentResponse(BaseModel):
    request_id: str
    status: Literal["completed", "blocked", "needs_input"]
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    trace: list[TraceStep] = Field(default_factory=list)


@dataclass
class AgentState:
    request_id: str
    request: AgentRequest
    intent: str = "unknown"
    plan: list[dict[str, Any]] = field(default_factory=list)
    context: list[Citation] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    trace: list[TraceStep] = field(default_factory=list)
    blocked_reason: str | None = None
