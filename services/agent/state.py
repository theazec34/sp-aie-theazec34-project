"""Brasaland LangGraph agent state (Parts 1–2)."""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict


class AgentState(TypedDict):
    """Minimal explicit state — no full chat history."""

    question: str
    chunks: list[dict[str, Any]]
    answer: str
    error: str | None
    empty_question: bool
    has_context: bool
    # Part 2 — routing + tool payloads
    intent: Literal["rag", "ticket", "inventory"]
    tool_ok: bool
    tool_result: dict[str, Any] | None
    sources_used: list[str]
    trace: list[dict[str, Any]]
    run_id: NotRequired[str]


RouteAfterReceive = Literal["retrieve", "ticket", "inventory", "refuse"]
RouteAfterRetrieve = Literal["generate", "refuse"]
RouteAfterTool = Literal["answer", "fallback"]
