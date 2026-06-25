from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GuardrailDecision:
    allowed: bool
    status: str
    reason: str


BLOCKED_TERMS = {
    "password",
    "credit card",
    "card number",
    "ssn",
    "social security",
    "api key",
    "secret",
    "token",
    "private key",
}

OUT_OF_SCOPE_TERMS = {
    "medical diagnosis",
    "legal advice",
    "investment advice",
}

PROMPT_INJECTION_TERMS = {
    "ignore previous",
    "ignore the previous",
    "system prompt",
    "developer message",
    "bypass guardrails",
    "reveal instructions",
    "override your instructions",
}

HUMAN_APPROVAL_TERMS = {
    "refund",
    "cancel account",
    "delete account",
    "change plan",
    "downgrade",
    "upgrade subscription",
    "issue credit",
}


def check_message(message: str) -> GuardrailDecision:
    normalized = message.strip().lower()

    if not normalized:
        return GuardrailDecision(
            allowed=False,
            status="blocked_malformed_request",
            reason="The request is empty or malformed.",
        )

    for term in BLOCKED_TERMS:
        if term in normalized:
            return GuardrailDecision(
                allowed=False,
                status="blocked_sensitive_data",
                reason="The request asks for sensitive data or credentials.",
            )

    for term in OUT_OF_SCOPE_TERMS:
        if term in normalized:
            return GuardrailDecision(
                allowed=False,
                status="blocked_out_of_scope",
                reason="The request is outside customer support scope.",
            )

    for term in PROMPT_INJECTION_TERMS:
        if term in normalized:
            return GuardrailDecision(
                allowed=False,
                status="blocked_prompt_injection",
                reason="The request appears to be trying to bypass the agent instructions.",
            )

    for term in HUMAN_APPROVAL_TERMS:
        if term in normalized:
            return GuardrailDecision(
                allowed=False,
                status="requires_human_approval",
                reason="Refunds, account changes, and credits require a human support owner.",
            )

    return GuardrailDecision(allowed=True, status="allowed", reason="Request is in support scope.")
