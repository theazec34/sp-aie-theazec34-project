"""Shared types for the agent security harness."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class FailureType(str, Enum):
    """Three failure categories the harness defends against."""

    STRUCTURAL = "structural"
    CONTENT = "content"
    SECURITY = "security"


class InputClass(str, Enum):
    DOMAIN = "domain"
    CASUAL = "casual"
    PERSONAL_TASK = "personal_task"
    JAILBREAK = "jailbreak"
    SENSITIVE_PROBE = "sensitive_probe"


GuardAction = Literal["allow", "redirect", "block"]


class GuardDecision(BaseModel):
    action: GuardAction
    input_class: InputClass
    failure_type: FailureType | None = None
    reason_code: str
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class OutputCheck(BaseModel):
    ok: bool
    failure_type: FailureType | None = None
    reason_code: str | None = None
    sanitized_answer: str
    blocked: bool = False
