from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Literal

from . import persistence

CaseStatus = Literal["Open", "In Progress", "Waiting on Customer", "Resolved"]


@dataclass
class Case:
    id: str
    customer_id: str
    title: str
    status: CaseStatus
    priority: str
    summary: str


@dataclass
class Customer:
    id: str
    name: str
    company: str
    email: str
    plan: str
    health_score: int
    last_seen: str
    cases: list[Case] = field(default_factory=list)
    history: list[str] = field(default_factory=list)


CUSTOMERS: dict[str, Customer] = {
    "cus-1001": Customer(
        id="cus-1001",
        name="Maya Chen",
        company="Northstar Solar",
        email="maya.chen@northstarsolar.example",
        plan="Pro",
        health_score=71,
        last_seen="2026-06-24",
        cases=[
            Case(
                id="case-501",
                customer_id="cus-1001",
                title="Invoice renewal card declined",
                status="Open",
                priority="High",
                summary="Renewal payment failed after card replacement. Customer needs invoice retry link.",
            ),
            Case(
                id="case-502",
                customer_id="cus-1001",
                title="Dashboard export delay",
                status="Waiting on Customer",
                priority="Medium",
                summary="Export job completed after retry; waiting for confirmation from Maya.",
            ),
        ],
        history=[
            "2026-06-18: Asked about annual Pro renewal and invoice recipients.",
            "2026-06-21: Reported card replacement after failed payment.",
            "2026-06-24: Export delay resolved after retry from support.",
        ],
    ),
    "cus-1002": Customer(
        id="cus-1002",
        name="Jordan Patel",
        company="Bluepeak Logistics",
        email="jordan.patel@bluepeak.example",
        plan="Enterprise",
        health_score=84,
        last_seen="2026-06-25",
        cases=[
            Case(
                id="case-601",
                customer_id="cus-1002",
                title="SSO certificate rotation",
                status="In Progress",
                priority="High",
                summary="Security team uploaded new SAML certificate and needs validation.",
            )
        ],
        history=[
            "2026-06-12: Enterprise QBR noted strong adoption in dispatch teams.",
            "2026-06-19: Requested SSO certificate rotation steps.",
            "2026-06-25: Shared new metadata file for support validation.",
        ],
    ),
    "cus-1003": Customer(
        id="cus-1003",
        name="Avery Brooks",
        company="Cedar Health",
        email="avery.brooks@cedarhealth.example",
        plan="Starter",
        health_score=49,
        last_seen="2026-06-20",
        cases=[
            Case(
                id="case-701",
                customer_id="cus-1003",
                title="Mobile login timeout",
                status="Open",
                priority="Medium",
                summary="Users see timeout on older Android devices after password reset.",
            )
        ],
        history=[
            "2026-05-28: Trial converted to Starter plan.",
            "2026-06-16: Password reset campaign triggered support questions.",
            "2026-06-20: Mobile timeout reported by three clinic users.",
        ],
    ),
}

_SEED_CUSTOMERS = deepcopy(CUSTOMERS)
_CASE_SEQUENCE = 800


def list_customers() -> list[Customer]:
    return deepcopy(list(CUSTOMERS.values()))


def get_customer(customer_id: str) -> Customer | None:
    customer = CUSTOMERS.get(customer_id)
    return deepcopy(customer) if customer else None


def create_case(customer_id: str, title: str, priority: str, summary: str) -> Case:
    global _CASE_SEQUENCE
    if customer_id not in CUSTOMERS:
        raise ValueError(f"Unknown customer id: {customer_id}")

    _CASE_SEQUENCE += 1
    case = Case(
        id=f"case-{_CASE_SEQUENCE}",
        customer_id=customer_id,
        title=title,
        status="Open",
        priority=priority,
        summary=summary,
    )
    CUSTOMERS[customer_id].cases.append(case)
    CUSTOMERS[customer_id].history.append(f"2026-06-25: Ticket {case.id} opened - {title}.")
    _persist("case_created", {"case_id": case.id, "customer_id": customer_id})
    return deepcopy(case)


def update_case_status(case_id: str, status: CaseStatus) -> Case:
    for customer in CUSTOMERS.values():
        for case in customer.cases:
            if case.id == case_id:
                case.status = status
                customer.history.append(f"2026-06-25: {case.id} status changed to {status}.")
                _persist("case_status_updated", {"case_id": case.id, "status": status})
                return deepcopy(case)
    raise ValueError(f"Unknown case id: {case_id}")


def reset_demo_data() -> None:
    global CUSTOMERS, _CASE_SEQUENCE
    CUSTOMERS = deepcopy(_ORIGINAL_CUSTOMERS)
    _CASE_SEQUENCE = 800
    _persist("demo_data_reset", {})


def _serialize_customers(customers: dict[str, Customer]) -> dict[str, dict]:
    return {customer_id: asdict(customer) for customer_id, customer in customers.items()}


def _hydrate_customers(payload: dict[str, dict]) -> dict[str, Customer]:
    hydrated: dict[str, Customer] = {}
    for customer_id, record in payload.items():
        cases = [Case(**case) for case in record.get("cases", [])]
        hydrated[customer_id] = Customer(
            id=record["id"],
            name=record["name"],
            company=record["company"],
            email=record["email"],
            plan=record["plan"],
            health_score=record["health_score"],
            last_seen=record["last_seen"],
            cases=cases,
            history=record.get("history", []),
        )
    return hydrated


def _persist(event_type: str, payload: dict) -> None:
    persistence.save_customers(_serialize_customers(CUSTOMERS))
    persistence.append_audit(event_type, payload)


if persistence.enabled():
    stored_customers = persistence.load_customers()
    if stored_customers:
        CUSTOMERS = _hydrate_customers(stored_customers)
        _CASE_SEQUENCE = max(
            [
                int(case.id.split("-")[1])
                for customer in CUSTOMERS.values()
                for case in customer.cases
                if case.id.startswith("case-") and case.id.split("-")[1].isdigit()
            ]
            or [_CASE_SEQUENCE]
        )
    else:
        persistence.save_customers(_serialize_customers(CUSTOMERS))


_ORIGINAL_CUSTOMERS = deepcopy(_SEED_CUSTOMERS)
