"""Brasaland LangGraph agent state (Parts 1–3 + memory + guardrails)."""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict


class AgentState(TypedDict):
    """Explicit state — session, memory, and guardrail fields."""

    question: str
    chunks: list[dict[str, Any]]
    answer: str
    error: str | None
    empty_question: bool
    has_context: bool
    # Part 2 — routing + tool payloads
    intent: Literal[
        "rag", "ticket", "inventory", "memory_confirm", "guard_block", "casual"
    ]
    tool_ok: bool
    tool_result: dict[str, Any] | None
    sources_used: list[str]
    trace: list[dict[str, Any]]
    run_id: NotRequired[str]
    # Part 3 — episodic memory
    session_id: NotRequired[str]
    user_id: NotRequired[str | None]
    memory_hits: NotRequired[list[dict[str, Any]]]
    memory_proposal: NotRequired[dict[str, Any] | None]
    memory_decision: NotRequired[str | None]
    pending_resolved: NotRequired[bool]
    # Part 4 — guardrails
    guard_action: NotRequired[str | None]
    guard_reason: NotRequired[str | None]
    guard_failure_type: NotRequired[str | None]


RouteAfterReceive = Literal[
    "retrieve", "ticket", "inventory", "refuse", "memory_confirm", "guard_block", "casual"
]
RouteAfterRetrieve = Literal["generate", "refuse"]
RouteAfterTool = Literal["answer", "fallback"]
