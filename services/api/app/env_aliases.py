"""Normalize env aliases early (LLM_* → GENERATION_* for portal 4Geeks)."""

from __future__ import annotations

import os


def apply_llm_env_aliases() -> None:
    aliases = (
        ("LLM_BASE_URL", "GENERATION_BASE_URL"),
        ("LLM_API_KEY", "GENERATION_API_KEY"),
        ("LLM_MODEL", "GENERATION_MODEL_ID"),
        ("LLM_MODEL_ID", "GENERATION_MODEL_ID"),
        ("LLM_TIMEOUT_SECONDS", "GENERATION_TIMEOUT_SECONDS"),
    )
    for src, dest in aliases:
        if os.getenv(dest, "").strip():
            continue
        val = os.getenv(src, "").strip()
        if val:
            os.environ[dest] = val
    if not os.getenv("GENERATION_PROVIDER", "").strip():
        if os.getenv("GENERATION_BASE_URL", "").strip() and (
            os.getenv("GENERATION_MODEL_ID", "").strip()
            or os.getenv("GENERATION_API_KEY", "").strip()
        ):
            os.environ["GENERATION_PROVIDER"] = "openai"
