from __future__ import annotations

from dataclasses import asdict
from typing import Any

from . import db


def lookup_customer(customer_id: str) -> dict[str, Any]:
    customer = db.get_customer(customer_id)
    if customer is None:
        raise ValueError(f"Unknown customer id: {customer_id}")
    return asdict(customer)


def create_ticket(customer_id: str, title: str, priority: str, summary: str) -> dict[str, Any]:
    case = db.create_case(customer_id=customer_id, title=title, priority=priority, summary=summary)
    return asdict(case)


def update_case_status(case_id: str, status: db.CaseStatus) -> dict[str, Any]:
    case = db.update_case_status(case_id=case_id, status=status)
    return asdict(case)


def summarize_history(customer_id: str) -> dict[str, str]:
    customer = db.get_customer(customer_id)
    if customer is None:
        raise ValueError(f"Unknown customer id: {customer_id}")

    open_cases = [case for case in customer.cases if case.status != "Resolved"]
    case_summary = "; ".join(f"{case.id}: {case.title} ({case.status})" for case in open_cases)
    timeline = " ".join(customer.history[-3:])
    return {
        "summary": f"{customer.name} at {customer.company} has {len(open_cases)} active case(s). {case_summary}. Recent history: {timeline}",
    }
