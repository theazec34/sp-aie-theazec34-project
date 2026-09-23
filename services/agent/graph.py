"""Compile the Brasaland agent graph — RAG + external tools (Parts 1–2)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    answer_from_inventory,
    answer_from_ticket,
    generate_response,
    lookup_inventory,
    lookup_ticket,
    receive_question,
    refuse_honestly,
    retrieve_knowledge,
    tool_fallback,
)
from agent.state import (
    AgentState,
    RouteAfterReceive,
    RouteAfterRetrieve,
    RouteAfterTool,
)


def route_after_receive(state: AgentState) -> RouteAfterReceive:
    if state.get("empty_question"):
        return "refuse"
    intent = state.get("intent") or "rag"
    if intent == "ticket":
        return "ticket"
    if intent == "inventory":
        return "inventory"
    return "retrieve"


def route_after_retrieve(state: AgentState) -> RouteAfterRetrieve:
    if not state.get("has_context") or not (state.get("chunks") or []):
        return "refuse"
    return "generate"


def route_after_tool(state: AgentState) -> RouteAfterTool:
    if state.get("tool_ok"):
        return "answer"
    return "fallback"


def build_agent_graph(*, checkpointer: MemorySaver | None = None):
    """Build and compile the graph (structural errors fail at compile time)."""
    builder = StateGraph(AgentState)

    builder.add_node("receive_question", receive_question)
    builder.add_node("retrieve_knowledge", retrieve_knowledge)
    builder.add_node("generate_response", generate_response)
    builder.add_node("refuse_honestly", refuse_honestly)
    builder.add_node("lookup_ticket", lookup_ticket)
    builder.add_node("answer_from_ticket", answer_from_ticket)
    builder.add_node("lookup_inventory", lookup_inventory)
    builder.add_node("answer_from_inventory", answer_from_inventory)
    builder.add_node("tool_fallback", tool_fallback)

    builder.add_edge(START, "receive_question")
    builder.add_conditional_edges(
        "receive_question",
        route_after_receive,
        {
            "retrieve": "retrieve_knowledge",
            "ticket": "lookup_ticket",
            "inventory": "lookup_inventory",
            "refuse": "refuse_honestly",
        },
    )
    builder.add_conditional_edges(
        "retrieve_knowledge",
        route_after_retrieve,
        {"generate": "generate_response", "refuse": "refuse_honestly"},
    )
    builder.add_conditional_edges(
        "lookup_ticket",
        route_after_tool,
        {"answer": "answer_from_ticket", "fallback": "tool_fallback"},
    )
    builder.add_conditional_edges(
        "lookup_inventory",
        route_after_tool,
        {"answer": "answer_from_inventory", "fallback": "tool_fallback"},
    )
    builder.add_edge("generate_response", END)
    builder.add_edge("refuse_honestly", END)
    builder.add_edge("answer_from_ticket", END)
    builder.add_edge("answer_from_inventory", END)
    builder.add_edge("tool_fallback", END)

    saver = checkpointer if checkpointer is not None else MemorySaver()
    return builder.compile(checkpointer=saver)


@lru_cache(maxsize=1)
def get_compiled_graph():
    return build_agent_graph()


def initial_state(question: str, *, run_id: str | None = None) -> AgentState:
    state: AgentState = {
        "question": question or "",
        "chunks": [],
        "answer": "",
        "error": None,
        "empty_question": False,
        "has_context": False,
        "intent": "rag",
        "tool_ok": False,
        "tool_result": None,
        "sources_used": [],
        "trace": [],
    }
    if run_id:
        state["run_id"] = run_id
    return state


def run_agent(question: str, *, run_id: str | None = None) -> dict[str, Any]:
    """Invoke compiled graph; persist consultable trace."""
    import uuid

    from agent.tracing import persist_trace

    rid = run_id or str(uuid.uuid4())
    graph = get_compiled_graph()
    config = {"configurable": {"thread_id": rid}}
    final = graph.invoke(initial_state(question, run_id=rid), config=config)

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
        "intent": final.get("intent"),
        "sources_used": list(final.get("sources_used") or []),
    }
    persist_trace(payload)
    return payload
