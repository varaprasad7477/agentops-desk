from __future__ import annotations

import re
import time
import uuid
from collections.abc import Callable

from .guardrails import GuardrailViolation, redact, validate_user_message
from .memory import MemoryStore
from .models import AgentRequest, AgentResponse, AgentState, TraceStep
from .retrieval import Retriever
from .tools import ToolError, ToolRegistry


class RuleBasedPlanner:
    """Deterministic baseline implementing the same structured plan contract as an LLM planner."""

    def plan(self, message: str) -> tuple[str, list[dict]]:
        ticket_match = re.search(r"\bT-\d+\b", message.upper())
        ticket_id = ticket_match.group(0) if ticket_match else None
        if not ticket_id:
            return "ticket_resolution", []
        steps = [{"tool": "get_ticket", "args": {"ticket_id": ticket_id}}]
        if "refund" in message.lower():
            steps.append({"tool": "draft_refund", "args": {"ticket_id": ticket_id}})
        return "ticket_resolution", steps


class AgentWorkflow:
    def __init__(self, memory: MemoryStore | None = None) -> None:
        self.memory = memory or MemoryStore()
        self.retriever = Retriever()
        self.tools = ToolRegistry()
        self.planner = RuleBasedPlanner()

    @staticmethod
    def _stage(state: AgentState, name: str, action: Callable[[], None]) -> None:
        start = time.perf_counter()
        status = "ok"
        detail = "completed"
        try:
            action()
        except (GuardrailViolation, ToolError) as exc:
            status = "blocked"
            detail = str(exc)
            state.blocked_reason = str(exc)
        except Exception:
            status = "error"
            detail = "internal workflow error"
            state.blocked_reason = detail
        state.trace.append(TraceStep(stage=name, status=status, detail=detail, duration_ms=round((time.perf_counter() - start) * 1000, 2)))

    def run(self, request: AgentRequest) -> AgentResponse:
        state = AgentState(request_id=str(uuid.uuid4()), request=request)

        self._stage(state, "guard", lambda: validate_user_message(request.message))
        if not state.blocked_reason:
            def make_plan() -> None:
                state.intent, state.plan = self.planner.plan(request.message)
                if not state.plan:
                    raise ToolError("Provide a ticket ID such as T-100")
            self._stage(state, "plan", make_plan)
        if not state.blocked_reason:
            self._stage(state, "retrieve", lambda: state.context.extend(self.retriever.search(request.message)))
        if not state.blocked_reason:
            def execute() -> None:
                for step in state.plan:
                    state.tool_results.append(self.tools.execute(step["tool"], step["args"], request.permissions))
            self._stage(state, "execute", execute)
        if not state.blocked_reason:
            self._stage(state, "verify", lambda: validate_user_message(" ".join(item.excerpt for item in state.context)))

        self.memory.append(request.session_id, "agent_run", {
            "request_id": state.request_id,
            "message": redact(request.message),
            "blocked": bool(state.blocked_reason),
            "tools": [result["tool"] for result in state.tool_results],
        })

        if state.blocked_reason:
            return AgentResponse(request_id=state.request_id, status="blocked", answer=state.blocked_reason, trace=state.trace)
        ticket = state.tool_results[0]["output"]
        refund = next((r["output"] for r in state.tool_results if r["tool"] == "draft_refund"), None)
        answer = f"Ticket {ticket['id']} is {ticket['status']} with {ticket['priority']} priority."
        if refund:
            answer += " A refund draft was created for human review." if refund["drafted"] else f" Refund not drafted: {refund['reason']}."
        return AgentResponse(
            request_id=state.request_id,
            status="completed",
            answer=answer,
            citations=state.context,
            tool_results=state.tool_results,
            trace=state.trace,
        )
