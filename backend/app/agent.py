from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from . import guardrails, prompts, tools


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]
    result_summary: str


@dataclass(frozen=True)
class AgentResult:
    answer: str
    safety_status: str
    tool_calls: list[ToolCall]


def run_agent(customer_id: str, message: str) -> AgentResult:
    decision = guardrails.check_message(message)
    if not decision.allowed:
        return AgentResult(
            answer=f"I cannot help with that request. {decision.reason}",
            safety_status=decision.status,
            tool_calls=[],
        )

    normalized = message.lower()
    tool_calls: list[ToolCall] = []
    try:
        customer = _call_tool(tool_calls, "lookup_customer", {"customer_id": customer_id})
    except ValueError:
        return AgentResult(
            answer="I cannot find that customer in the CRM. Please verify the customer id before taking action.",
            safety_status="blocked_unknown_customer",
            tool_calls=[],
        )

    if _should_summarize(normalized):
        _call_tool(tool_calls, "summarize_history", {"customer_id": customer_id})

    if _should_update_status(normalized):
        case_id = _extract_case_id(message) or _first_case_id(customer)
        status = _extract_status(normalized)
        _call_tool(tool_calls, "update_case_status", {"case_id": case_id, "status": status})

    created_ticket = None
    if _should_create_ticket(normalized):
        created_ticket = _call_tool(
            tool_calls,
            "create_ticket",
            {
                "customer_id": customer_id,
                "title": _ticket_title(normalized),
                "priority": _priority(normalized),
                "summary": _ticket_summary(message),
            },
        )

    prompt = prompts.render_answer_prompt(
        customer_context=f"{customer['name']} at {customer['company']} on {customer['plan']} plan.",
        tool_trace="\n".join(f"{call.name}: {call.result_summary}" for call in tool_calls),
        message=message,
    )
    answer = _compose_answer(prompt, customer, tool_calls, created_ticket)
    return AgentResult(answer=answer, safety_status=decision.status, tool_calls=tool_calls)


def _call_tool(tool_calls: list[ToolCall], name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    registry = {
        "lookup_customer": tools.lookup_customer,
        "create_ticket": tools.create_ticket,
        "update_case_status": tools.update_case_status,
        "summarize_history": tools.summarize_history,
    }
    result = registry[name](**arguments)
    summary = _summarize_tool_result(name, result)
    tool_calls.append(ToolCall(name=name, arguments=arguments, result_summary=summary))
    return result


def _summarize_tool_result(name: str, result: dict[str, Any]) -> str:
    if name == "lookup_customer":
        return f"Loaded {result['name']} at {result['company']} with {len(result['cases'])} case(s)."
    if name == "create_ticket":
        return f"Created {result['id']} with {result['priority']} priority."
    if name == "update_case_status":
        return f"Updated {result['id']} to {result['status']}."
    if name == "summarize_history":
        return result["summary"]
    return json.dumps(result)


def _should_summarize(message: str) -> bool:
    return any(term in message for term in ["summary", "summarize", "history", "context", "recap"])


def _should_create_ticket(message: str) -> bool:
    return any(term in message for term in ["create ticket", "open ticket", "new ticket", "escalate", "complaint", "broken", "failed"])


def _should_update_status(message: str) -> bool:
    return any(term in message for term in ["mark", "set", "update status", "resolve", "resolved", "close case"])


def _extract_case_id(message: str) -> str | None:
    match = re.search(r"case-\d+", message.lower())
    return match.group(0) if match else None


def _extract_status(message: str) -> str:
    if "waiting" in message.lower():
        return "Waiting on Customer"
    if "progress" in message.lower():
        return "In Progress"
    if "resolved" in message.lower() or "resolve" in message.lower() or "close" in message.lower():
        return "Resolved"
    return "In Progress"


def _first_case_id(customer: dict[str, Any]) -> str:
    cases = customer.get("cases", [])
    if not cases:
        raise ValueError("Customer has no cases to update.")
    return cases[0]["id"]


def _ticket_title(message: str) -> str:
    if "billing" in message or "invoice" in message or "payment" in message:
        return "Billing support follow-up"
    if "login" in message or "sso" in message:
        return "Authentication support follow-up"
    return "Customer support follow-up"


def _priority(message: str) -> str:
    if any(term in message for term in ["urgent", "blocked", "failed", "escalate", "enterprise"]):
        return "High"
    return "Medium"


def _ticket_summary(message: str) -> str:
    cleaned = " ".join(message.split())
    return cleaned[:220]


def _compose_answer(
    rendered_prompt: str,
    customer: dict[str, Any],
    tool_calls: list[ToolCall],
    created_ticket: dict[str, Any] | None,
) -> str:
    del rendered_prompt
    action_lines = [call.result_summary for call in tool_calls if call.name != "lookup_customer"]
    if created_ticket:
        action_lines.append(f"Ticket {created_ticket['id']} is ready for the support queue.")

    active_cases = [case for case in customer["cases"] if case["status"] != "Resolved"]
    case_text = f"{len(active_cases)} active case(s)" if active_cases else "no active cases"
    actions = " ".join(action_lines) if action_lines else "No CRM state change was needed."
    return (
        f"I found {customer['name']} from {customer['company']} on the {customer['plan']} plan with "
        f"{case_text}. {actions} Recommended next step: send a concise update and confirm ownership."
    )
