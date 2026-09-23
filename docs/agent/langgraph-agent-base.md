# Brasaland LangGraph Agent — Part 1 (base)

Wraps the existing RAG pipeline (`retrieve` + `generate_answer`) as an explicit
state machine. Does **not** call monolithic `query()` inside a single node.

## Graph

```text
START → receive_question
           ├─(empty)──► refuse_honestly → END
           └─(ok)─────► retrieve_knowledge
                            ├─(no chunks)─► refuse_honestly → END
                            └─(has ctx)───► generate_response → END
```

| Node | Responsibility | Reuses |
|------|----------------|--------|
| `receive_question` | Normalize / validate | — |
| `retrieve_knowledge` | KB search | `data.pipelines.rag.retrieve` |
| `generate_response` | LLM / grounded answer | `data.pipelines.rag.generate_answer` |
| `refuse_honestly` | Honest refusal | `refusal_message()` |

- **State:** minimal (`question`, `chunks`, `answer`, flags, `trace`) — no chat history.
- **Compile:** `build_agent_graph()` / `get_compiled_graph()` before invoke.
- **Checkpointing:** `MemorySaver` with `thread_id=run_id` on every run.
- **Traces:** `data/eval/agent_traces/{run_id}.json` (+ `index.jsonl`).

## API

- `POST /agent/query` → `{ answer, run_id, nodes, checkpointed }`
- `GET /agent/traces/{run_id}` → persisted trace

## Tests

```bash
uv run pytest tests/pipelines/test_agent_graph.py tests/pipelines/test_rag.py -q
```
