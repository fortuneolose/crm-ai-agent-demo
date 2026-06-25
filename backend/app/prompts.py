SYSTEM_PROMPT = """You are a customer support AI agent embedded in a CRM console.
Use approved CRM tools before answering questions about customers, cases, or account history.
Never expose secrets, raw credentials, payment card data, or private security tokens.
When an action changes CRM state, state the action plainly and keep the answer concise."""

ANSWER_TEMPLATE = """Customer context:
{customer_context}

Tool trace:
{tool_trace}

User request:
{message}

Write a concise support-agent response with next steps."""


def render_answer_prompt(customer_context: str, tool_trace: str, message: str) -> str:
    return ANSWER_TEMPLATE.format(
        customer_context=customer_context,
        tool_trace=tool_trace,
        message=message,
    )
