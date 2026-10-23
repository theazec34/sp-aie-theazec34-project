"""BrasAI reindex job — background status machine."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_SERVICES = _REPO / "services"
for _p in (_REPO, _SERVICES):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def test_reindex_job_start_and_done(monkeypatch: pytest.MonkeyPatch):
    import knowledge.reindex_job as job

    def _slow_setup(*, recreate=False):
        time.sleep(0.15)
        return {
            "collection": "brasaland_knowledge",
            "chunks_indexed": 3,
        }

    monkeypatch.setattr("data.process.rag.setup", _slow_setup)
    # reset module state
    with job._lock:  # noqa: SLF001
        job._state.update(  # noqa: SLF001
            {
                "status": "idle",
                "started_at": None,
                "finished_at": None,
                "result": None,
                "error": None,
            }
        )

    started = job.start_reindex(recreate=True)
    assert started["status"] == "running"

    # second start while running is a no-op
    again = job.start_reindex(recreate=True)
    assert again["status"] == "running"

    deadline = time.time() + 3
    while time.time() < deadline:
        st = job.get_status()
        if st["status"] in {"done", "error"}:
            break
        time.sleep(0.05)

    final = job.get_status()
    assert final["status"] == "done"
    assert final["result"]["chunks_indexed"] == 3
