"""Security harness & guardrails for the Manager support agent."""

from agent.guardrails.harness import (
    SECURE_SYSTEM_PROMPT,
    build_generation_messages,
    guard_answer,
    guard_user_input,
    prepare_rag_context,
    prepare_tool_result,
)
from agent.guardrails.observability import guardrail_summary, reset_guardrail_stats_for_tests
from agent.guardrails.types import FailureType, GuardDecision, InputClass

__all__ = [
    "SECURE_SYSTEM_PROMPT",
    "FailureType",
    "GuardDecision",
    "InputClass",
    "build_generation_messages",
    "guard_answer",
    "guard_user_input",
    "guardrail_summary",
    "prepare_rag_context",
    "prepare_tool_result",
    "reset_guardrail_stats_for_tests",
]
