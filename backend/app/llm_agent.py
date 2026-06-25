from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from . import config, guardrails, prompts
from .agent import AgentResult, ToolCall, _call_tool, _compose_answer

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "lookup_customer",
        "description": "Lookup CRM account, cases, and recent support history for one customer.",
        "parameters": {
            "type": "object",
            "properties": {"customer_id": {"type": "string"}},
            "required": ["customer_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "summarize_history",
        "description": "Summarize recent support history and active cases for one customer.",
        "parameters": {
            "type": "object",
            "properties": {"customer_id": {"type": "string"}},
            "required": ["customer_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "create_ticket",
        "description": "Create a support ticket that still requires normal human queue ownership.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "title": {"type": "string"},
                "priority": {"type": "string", "enum": ["Low", "Medium", "High"]},
                "summary": {"type": "string"},
            },
            "required": ["customer_id", "title", "priority", "summary"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "update_case_status",
        "description": "Update a case status when the support owner confirms the target case.",
        "parameters": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["Open", "In Progress", "Waiting on Customer", "Resolved"],
                },
            },
            "required": ["case_id", "status"],
            "additionalProperties": False,
        },
    },
]


def run_hosted_agent(customer_id: str, message: str) -> AgentResult:
    decision = guardrails.check_message(message)
    if not decision.allowed:
        return AgentResult(
            answer=f"I cannot help with that request. {decision.reason}",
            safety_status=decision.status,
            tool_calls=[],
        )

    api_key = config.openai_api_key()
    model = config.openai_model()
    if not api_key or not model:
        return AgentResult(
            answer=(
                "Hosted LLM mode is enabled but OPENAI_API_KEY and OPENAI_MODEL are not both set. "
                "Switch AGENT_MODE to deterministic or configure those environment variables."
            ),
            safety_status="blocked_missing_llm_config",
            tool_calls=[],
        )

    tool_calls: list[ToolCall] = []
    initial_response = _openai_request(
        api_key,
        {
            "model": model,
            "instructions": prompts.SYSTEM_PROMPT,
            "input": (
                f"Customer id: {customer_id}\n"
                f"Support request: {message}\n"
                "Use CRM tools before answering. Never use a different customer_id than the one provided."
            ),
            "tools": TOOL_SCHEMAS,
        },
    )

    tool_outputs = _execute_requested_tools(initial_response, customer_id, tool_calls)
    if tool_outputs:
        final_response = _openai_request(
            api_key,
            {
                "model": model,
                "previous_response_id": initial_response.get("id"),
                "input": tool_outputs,
            },
        )
        answer = _response_text(final_response)
    else:
        answer = _response_text(initial_response)

    if answer:
        return AgentResult(answer=answer, safety_status=decision.status, tool_calls=tool_calls)

    customer = _call_tool(tool_calls, "lookup_customer", {"customer_id": customer_id})
    fallback = _compose_answer("", customer, tool_calls, None)
    return AgentResult(answer=fallback, safety_status=decision.status, tool_calls=tool_calls)


def _execute_requested_tools(
    response: dict[str, Any],
    customer_id: str,
    tool_calls: list[ToolCall],
) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for item in response.get("output", []):
        if item.get("type") != "function_call":
            continue

        name = item.get("name")
        if name not in {schema["name"] for schema in TOOL_SCHEMAS}:
            continue

        arguments = json.loads(item.get("arguments") or "{}")
        if "customer_id" in arguments:
            arguments["customer_id"] = customer_id

        result = _call_tool(tool_calls, name, arguments)
        outputs.append(
            {
                "type": "function_call_output",
                "call_id": item["call_id"],
                "output": json.dumps(result),
            }
        )

    return outputs


def _openai_request(api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI Responses API request failed: {exc.code} {body}") from exc


def _response_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]

    chunks: list[str] = []
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])
    return "\n".join(chunks).strip()
