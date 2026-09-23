"""Brasaland LangGraph agent — Part 1 (langgraph-agent-base).

Wraps existing RAG ``retrieve`` / ``generate_answer`` as separate nodes.
Does **not** call monolithic ``query()`` inside a single node.
"""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict


class AgentState(TypedDict):
    """Minimal explicit state passed between graph nodes.

    No full conversation history — only what nodes need to decide/route.
    """

    question: str
    chunks: list[dict[str, Any]]
    answer: str
    error: str | None
    # Routing / outcome flags
    empty_question: bool
    has_context: bool
    # Append-only execution trace (also persisted to disk after the run)
    trace: list[dict[str, Any]]
    # Optional run id for checkpoint thread + trace file
    run_id: NotRequired[str]


RouteAfterReceive = Literal["retrieve", "refuse"]
RouteAfterRetrieve = Literal["generate", "refuse"]
