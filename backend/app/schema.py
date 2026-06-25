from __future__ import annotations

import json

import strawberry

from . import agent, db


@strawberry.type
class CaseType:
    id: str
    customer_id: str
    title: str
    status: str
    priority: str
    summary: str


@strawberry.type
class CustomerType:
    id: str
    name: str
    company: str
    email: str
    plan: str
    health_score: int
    last_seen: str
    cases: list[CaseType]
    history: list[str]


@strawberry.type
class ToolCallType:
    name: str
    arguments: str
    result_summary: str


@strawberry.type
class AgentResponse:
    answer: str
    safety_status: str
    tool_calls: list[ToolCallType]


@strawberry.input
class AgentRequest:
    customer_id: str
    message: str


def _case_to_type(case: db.Case) -> CaseType:
    return CaseType(**case.__dict__)


def _customer_to_type(customer: db.Customer) -> CustomerType:
    return CustomerType(
        id=customer.id,
        name=customer.name,
        company=customer.company,
        email=customer.email,
        plan=customer.plan,
        health_score=customer.health_score,
        last_seen=customer.last_seen,
        cases=[_case_to_type(case) for case in customer.cases],
        history=customer.history,
    )


@strawberry.type
class Query:
    @strawberry.field
    def customers(self) -> list[CustomerType]:
        return [_customer_to_type(customer) for customer in db.list_customers()]

    @strawberry.field
    def customer(self, customer_id: str) -> CustomerType | None:
        customer = db.get_customer(customer_id)
        return _customer_to_type(customer) if customer else None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def ask_agent(self, request: AgentRequest) -> AgentResponse:
        result = agent.run_agent(customer_id=request.customer_id, message=request.message)
        return AgentResponse(
            answer=result.answer,
            safety_status=result.safety_status,
            tool_calls=[
                ToolCallType(
                    name=call.name,
                    arguments=json.dumps(call.arguments),
                    result_summary=call.result_summary,
                )
                for call in result.tool_calls
            ],
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)
