from __future__ import annotations

import os


def agent_mode() -> str:
    return os.getenv("AGENT_MODE", "deterministic").strip().lower()


def openai_api_key() -> str | None:
    return os.getenv("OPENAI_API_KEY")


def openai_model() -> str | None:
    return os.getenv("OPENAI_MODEL")
