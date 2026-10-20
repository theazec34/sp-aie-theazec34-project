"""NIST Protect — rate limit en POST /agent/query (endpoint que invoca el modelo)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_limiter():
    from app.rate_limit import agent_query_limiter

    agent_query_limiter.reset_for_tests()
    # Ventana corta y cupo bajo para el test
    agent_query_limiter.max_calls = 3
    agent_query_limiter.window_seconds = 60.0
    yield
    agent_query_limiter.reset_for_tests()
    agent_query_limiter.max_calls = 20
    agent_query_limiter.window_seconds = 60.0


def test_agent_query_rate_limited(
    client: TestClient,
    auth_header: dict[str, str],
):
    fake = {
        "answer": "ok",
        "run_id": "r-rl",
        "session_id": "s-rl",
        "nodes": ["receive_question"],
        "checkpointed": False,
        "intent": "rag",
        "sources_used": [],
        "guard_action": None,
        "guard_reason": None,
        "guard_failure_type": None,
        "memory_proposal": None,
        "memory_decision": None,
        "error": None,
    }
    with patch("agent.router.run_agent", return_value=fake):
        for i in range(3):
            res = client.post(
                "/agent/query",
                headers=auth_header,
                json={"question": f"pregunta {i}", "session_id": "s-rl"},
            )
            assert res.status_code == 200, res.text

        blocked = client.post(
            "/agent/query",
            headers=auth_header,
            json={"question": "una más", "session_id": "s-rl"},
        )
        assert blocked.status_code == 429
        detail = blocked.json().get("detail", "")
        assert "ímite" in detail.lower() or "limit" in detail.lower()
        assert blocked.headers.get("Retry-After")
