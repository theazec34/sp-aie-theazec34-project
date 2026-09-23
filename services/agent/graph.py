"""Compile the Brasaland knowledge agent graph (LangGraph)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    generate_response,
    receive_question,
    refuse_honestly,
    retrieve_knowledge,
)
from agent.state import AgentState, RouteAfterReceive, RouteAfterRetrieve


def route_after_receive(state: AgentState) -> RouteAfterReceive:
    """Conditional edge: empty question → refuse; else → retrieve."""
    if state.get("empty_question"):
        return "refuse"
    return "retrieve"


def route_after_retrieve(state: AgentState) -> RouteAfterRetrieve:
    """Conditional edge: no chunks above threshold → refuse; else → generate."""
    if not state.get("has_context") or not (state.get("chunks") or []):
        return "refuse"
    return "generate"


def build_agent_graph(*, checkpointer: MemorySaver | None = None):
    """Build and **compile** the graph (fails fast on structural errors)."""
    builder = StateGraph(AgentState)

    builder.add_node("receive_question", receive_question)
    builder.add_node("retrieve_knowledge", retrieve_knowledge)
    builder.add_node("generate_response", generate_response)
    builder.add_node("refuse_honestly", refuse_honestly)

    builder.add_edge(START, "receive_question")
    builder.add_conditional_edges(
        "receive_question",
        route_after_receive,
        {
            "retrieve": "retrieve_knowledge",
            "refuse": "refuse_honestly",
        },
    )
    builder.add_conditional_edges(
        "retrieve_knowledge",
        route_after_retrieve,
        {
            "generate": "generate_response",
            "refuse": "refuse_honestly",
        },
    )
    builder.add_edge("generate_response", END)
    builder.add_edge("refuse_honestly", END)

    saver = checkpointer if checkpointer is not None else MemorySaver()
    return builder.compile(checkpointer=saver)


@lru_cache(maxsize=1)
def get_compiled_graph():
    """Process-wide compiled graph with in-memory checkpointing."""
    return build_agent_graph()


def initial_state(question: str, *, run_id: str | None = None) -> AgentState:
    state: AgentState = {
        "question": question or "",
        "chunks": [],
        "answer": "",
        "error": None,
        "empty_question": False,
        "has_context": False,
        "trace": [],
    }
    if run_id:
        state["run_id"] = run_id
    return state


def run_agent(question: str, *, run_id: str | None = None) -> dict[str, Any]:
    """Invoke the compiled graph; returns answer + consultable trace."""
    import uuid

    from agent.tracing import persist_trace

    rid = run_id or str(uuid.uuid4())
    graph = get_compiled_graph()
    config = {"configurable": {"thread_id": rid}}
    final = graph.invoke(initial_state(question, run_id=rid), config=config)

    # Checkpoint verification: load latest checkpoint for this thread
    checkpoint_ok = False
    try:
        snap = graph.get_state(config)
        checkpoint_ok = snap is not None and snap.values is not None
    except Exception:  # noqa: BLE001
        checkpoint_ok = False

    trace = list(final.get("trace") or [])
    payload = {
        "run_id": rid,
        "answer": final.get("answer") or "",
        "error": final.get("error"),
        "trace": trace,
        "nodes": [t.get("node") for t in trace],
        "checkpointed": checkpoint_ok,
        "n_chunks": len(final.get("chunks") or []),
    }
    persist_trace(payload)
    return payload
