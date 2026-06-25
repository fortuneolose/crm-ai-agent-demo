from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "crm_demo.sqlite"


def enabled() -> bool:
    return os.getenv("CRM_STORAGE", "memory").strip().lower() == "sqlite"


def db_path() -> Path:
    return Path(os.getenv("CRM_SQLITE_PATH", str(DEFAULT_DB_PATH))).resolve()


def load_customers() -> dict[str, Any] | None:
    if not enabled() or not db_path().exists():
        return None

    with _connect() as connection:
        _ensure_schema(connection)
        row = connection.execute(
            "select payload from crm_snapshot where id = ?",
            ("customers",),
        ).fetchone()
    return json.loads(row[0]) if row else None


def save_customers(payload: dict[str, Any]) -> None:
    if not enabled():
        return

    with _connect() as connection:
        _ensure_schema(connection)
        connection.execute(
            """
            insert into crm_snapshot (id, payload)
            values (?, ?)
            on conflict(id) do update set payload = excluded.payload
            """,
            ("customers", json.dumps(payload, sort_keys=True)),
        )


def append_audit(event_type: str, payload: dict[str, Any]) -> None:
    if not enabled():
        return

    with _connect() as connection:
        _ensure_schema(connection)
        connection.execute(
            "insert into audit_log (event_type, payload) values (?, ?)",
            (event_type, json.dumps(payload, sort_keys=True)),
        )


def _connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path)


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        create table if not exists crm_snapshot (
            id text primary key,
            payload text not null
        )
        """
    )
    connection.execute(
        """
        create table if not exists audit_log (
            id integer primary key autoincrement,
            event_type text not null,
            payload text not null,
            created_at text not null default current_timestamp
        )
        """
    )
