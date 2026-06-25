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


def check_message(message: str) -> GuardrailDecision:
    normalized = message.lower()

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

    return GuardrailDecision(allowed=True, status="allowed", reason="Request is in support scope.")
