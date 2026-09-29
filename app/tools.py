from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


class ToolError(ValueError):
    pass


@dataclass(frozen=True)
class Tool:
    name: str
    permission: str
    required_fields: frozenset[str]
    handler: Callable[[dict[str, Any]], dict[str, Any]]


TICKETS = {
    "T-100": {"id": "T-100", "priority": "high", "customer": "Demo Customer", "amount_inr": 2400, "status": "open"},
    "T-200": {"id": "T-200", "priority": "normal", "customer": "Sample User", "amount_inr": 6200, "status": "open"},
}


def get_ticket(args: dict[str, Any]) -> dict[str, Any]:
    ticket_id = str(args["ticket_id"]).upper()
    if ticket_id not in TICKETS:
        raise ToolError("Ticket not found")
    return TICKETS[ticket_id]


def draft_refund(args: dict[str, Any]) -> dict[str, Any]:
    ticket = get_ticket(args)
    if ticket["amount_inr"] >= 5000:
        return {"drafted": False, "reason": "Human approval required", "ticket_id": ticket["id"]}
    return {"drafted": True, "ticket_id": ticket["id"], "amount_inr": ticket["amount_inr"], "payment_executed": False}


class ToolRegistry:
    def __init__(self) -> None:
        self.tools = {
            "get_ticket": Tool("get_ticket", "ticket:read", frozenset({"ticket_id"}), get_ticket),
            "draft_refund": Tool("draft_refund", "refund:draft", frozenset({"ticket_id"}), draft_refund),
        }

    def execute(self, name: str, args: dict[str, Any], permissions: set[str]) -> dict[str, Any]:
        tool = self.tools.get(name)
        if not tool:
            raise ToolError(f"Unknown tool: {name}")
        if tool.permission not in permissions:
            raise ToolError(f"Missing permission: {tool.permission}")
        missing = tool.required_fields - args.keys()
        if missing:
            raise ToolError(f"Missing fields: {sorted(missing)}")
        return {"tool": name, "output": tool.handler(args)}
