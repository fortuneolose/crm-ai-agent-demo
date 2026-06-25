# Customer Support AI Agent

A Salesforce-style AI agent demo for customer support workflows. It shows a React + TypeScript console, a Python/FastAPI backend, a GraphQL API, a mock CRM database, explicit tool calls, guardrails, prompt templates, and evaluation tests for correct tool use.

![Customer support AI agent console](docs/assets/screenshots/01-crm-console-overview.png)

## Demo

Watch the silent MP4 walkthrough:

[Customer Support AI Agent Demo](docs/assets/recordings/customer-support-ai-agent-demo.mp4)

The demo covers the main agentic workflow:

- CRM account lookup and customer context loading.
- History summarization through `summarize_history`.
- Escalation and ticket creation through `create_ticket`.
- Case status changes through `update_case_status`.
- Guardrail refusal before tool execution for sensitive-data requests.

## What It Demonstrates

- React + TypeScript frontend with a CRM-style support workspace.
- FastAPI backend with a GraphQL endpoint at `/graphql`.
- Mock CRM/customer database with customers, cases, plans, and interaction history.
- Agentic workflow with auditable tool calls:
  - `lookup_customer`
  - `create_ticket`
  - `update_case_status`
  - `summarize_history`
- Prompt templates and deterministic guardrails.
- Evaluation tests that verify correct tool use and safe refusal behavior.

## Architecture

![Architecture diagram](docs/assets/architecture.svg)

```mermaid
flowchart LR
  User[Support Agent] --> UI[React + TypeScript Console]
  UI -->|GraphQL mutation| API[FastAPI /graphql]
  API --> Agent[Support Agent Orchestrator]
  Agent --> Guardrails[Prompt + Guardrails]
  Agent --> Tools[Tool Registry]
  Tools --> CRM[Mock CRM Database]
  CRM --> Tools
  Tools --> Agent
  Agent --> API
  API --> UI
```

## Agent Modes

The default mode is deterministic and intentionally does not require API keys. It is useful for demos, CI, and tool-use evaluations because the exact tool trace is reproducible.

Hosted LLM mode is optional:

```powershell
$env:AGENT_MODE="hosted_llm"
$env:OPENAI_API_KEY="..."
$env:OPENAI_MODEL="..."
uvicorn app.main:app --reload --port 8000
```

In hosted mode, the backend sends CRM tool schemas to the OpenAI Responses API, executes requested CRM tools server-side, and sends tool outputs back for the final answer. Guardrails still run before the hosted call. Leave `AGENT_MODE` unset to use deterministic mode.

## Optional SQLite Persistence

By default, CRM data is seeded in memory. To persist CRM snapshots and audit mutation events locally:

```powershell
$env:CRM_STORAGE="sqlite"
$env:CRM_SQLITE_PATH=".\data\crm_demo.sqlite"
uvicorn app.main:app --reload --port 8000
```

The SQLite file is ignored by Git.

## Repository Layout

```text
backend/
  app/
    agent.py          # tool-calling workflow and response generation
    db.py             # in-memory CRM data
    guardrails.py     # safety and scope checks
    main.py           # FastAPI app and GraphQL router
    prompts.py        # prompt templates
    schema.py         # Strawberry GraphQL schema
    tools.py          # CRM tool functions
  tests/
    test_agent_eval.py
frontend/
  src/
    App.tsx
    api.ts
    main.tsx
    styles.css
docs/
  assets/
    recordings/
      customer-support-ai-agent-demo.mp4
    screenshots/
      01-crm-console-overview.png
      02-history-summary-tool-call.png
      03-ticket-creation-trace.png
      04-case-status-update.png
      05-guardrail-refusal.png
  scripts/
    capture-demo.cjs
```

## Run Locally

### Backend

```powershell
cd customer-support-ai-agent\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

GraphQL playground:

```text
http://localhost:8000/graphql
```

### Frontend

```powershell
cd customer-support-ai-agent\frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## Example GraphQL Mutation

```graphql
mutation {
  askAgent(
    request: {
      customerId: "cus-1001"
      message: "Maya says billing failed after the Pro renewal. Can you summarize history and open a ticket?"
    }
  ) {
    answer
    safetyStatus
    toolCalls {
      name
      arguments
      resultSummary
    }
  }
}
```

## Evaluation Tests

The tests validate agent behavior at the tool-call level, not just natural-language output:

```powershell
cd customer-support-ai-agent\backend
pytest
```

Coverage includes:

- Billing/history questions call `lookup_customer` and `summarize_history`.
- Complaint/escalation requests create a ticket.
- Status-change requests call `update_case_status`.
- Unsafe or out-of-scope requests are refused without touching CRM tools.
- Prompt-injection attempts are blocked before tool execution.
- Unknown customer IDs fail closed without mutation tools.
- Refunds, credits, and account changes require human approval.
- Hosted LLM mode fails closed unless API configuration is explicit.

## CI

GitHub Actions runs backend `pytest`, frontend `npm run typecheck`, and frontend `npm run build` on pushes and pull requests to `main`.

## Screenshots

### CRM Console Overview

![CRM console overview](docs/assets/screenshots/01-crm-console-overview.png)

### History Summary Tool Call

![History summary tool call](docs/assets/screenshots/02-history-summary-tool-call.png)

### Ticket Creation Trace

![Ticket creation trace](docs/assets/screenshots/03-ticket-creation-trace.png)

### Case Status Update

![Case status update](docs/assets/screenshots/04-case-status-update.png)

### Guardrail Refusal

![Guardrail refusal](docs/assets/screenshots/05-guardrail-refusal.png)

## Regenerate Demo Media

Start the backend and frontend, then run:

```powershell
node docs\scripts\capture-demo.cjs
```

The script drives the live UI with Playwright, captures screenshots, records a WebM session, and converts it to MP4 with `ffmpeg`.

## How I Used AI Tools Responsibly

- I kept the mock agent deterministic so reviewers can run it without API keys or hidden model behavior.
- I treated AI as an implementation assistant, then encoded important behavior as tests.
- I avoided storing secrets, real customer data, or credentials in the repository.
- I made the agent's tool calls visible in the UI so users can inspect what happened before trusting the answer.
- I documented guardrails and failure modes instead of presenting the demo as production-ready automation.

## Production Next Steps

- Replace the deterministic planner with a hosted LLM tool-calling loop.
- Add OAuth, audit logging, and role-based permissions.
- Persist CRM data in Postgres.
- Add human approval before high-impact actions such as refunds or account changes.
- Expand evaluations with regression datasets and prompt-injection probes.
