# Brasaland RAG Knowledge Base — Design

**Hito:** RAG y Base de Conocimiento (CONTEXT `docs/rag/CONTEXT-brasaland.es.md`)  
**Colección Qdrant:** `brasaland_knowledge`  
**Corpus:** `docs/company-knowledge-base/*.es.md`

---

## 1. Proceso RAG (extremo a extremo)

1. Copiar manuales desde `00-general-contexts/brasaland/` → `docs/company-knowledge-base/`.
2. `setup()` (`data/process/rag.py`) lee el corpus, hace chunking semántico e indexa.
3. `embed(chunk)` genera el vector con el **modelo de embeddings** (nunca el de generación).
4. Upsert a Qdrant colección `brasaland_knowledge` con IDs UUID5 deterministas + payload CONTEXT.
5. En consulta: `POST /knowledge/query` → `query(question)`.
6. `retrieve()` reutiliza el mismo `embed()` sobre la pregunta, busca top-`k`, filtra `min_score`.
7. `generate_answer(question, context)` arma el prompt (voz de vendedor Brasaland) y llama al **LLM de generación**.
8. La API/UI devuelven solo `{ "answer": "..." }` — nunca chunks crudos ni scores.

```text
docs/company-knowledge-base/*.md
        │
        ▼
   setup() → embed() → Qdrant (brasaland_knowledge)
                              ▲
                              │
question → embed() → retrieve() → generate_answer() → answer
```

---

## 2. Estrategia de chunking

Los cuatro manuales son Markdown corto en español, con títulos `H1` y bloques etiquetados (`Niveles del programa:`, `Procedimiento diario:`, etc.) más que `##` consistentes.

**Enfoque híbrido:**

1. **Primario:** cortes en headings `#`/`##`/`###` o en etiquetas de sección conocidas del corpus ES.
2. **Guardia de longitud:** secciones > ~1000 caracteres se parten por párrafos (línea en blanco), nunca a mitad de frase/regla.
3. **Densidad mínima:** `_ensure_min_chunks()` garantiza ≥ 3 chunks por documento (requisito CONTEXT).

**Por qué encaja:** mantiene intactas tablas de niveles, listas de alérgenos y pasos de protocolo — unidades semánticas que las preguntas de gerentes suelen citar.

**Conteo aproximado (corpus actual):** ~3–5 chunks por documento (total ~14–16 tras indexar).

**Idempotencia:** IDs `uuid5(namespace, source_document:chunk_index:section)` + upsert. Opcionalmente `--recreate` hace clear-and-reload.

---

## 3. Prácticas de embedding y recuperación

| Rol | Variables | Modelo por defecto en este monorepo |
| --- | --------- | ----------------------------------- |
| Embeddings | `EMBEDDING_PROVIDER`, `EMBEDDING_BASE_URL`, `EMBEDDING_API_KEY`, `EMBEDDING_MODEL_ID` | `fastembed` + `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (gratis/local). Con portal 4Geeks: `EMBEDDING_PROVIDER=openai` + IDs del portal (p. ej. `…/pplx-embed-…`). |
| Generación | `GENERATION_PROVIDER`, `GENERATION_BASE_URL`, `GENERATION_API_KEY`, `GENERATION_MODEL_ID` | Portal 4Geeks chat (`openai`). Sin credenciales: `grounded` (respuesta armada solo con texto recuperado — para DX; producción debe usar LLM). |

- **Misma** función `embed()` en indexación y en query.
- **Dimensión:** la de la primera llamada a `embed()` al crear la colección (MiniLM multilingual ≈ **384**).
- **Distancia Qdrant:** Cosine.
- **`min_score` por defecto:** `0.32` (`RAG_MIN_SCORE`). Scores on-topic del corpus ES con MiniLM suelen caer ~0.35–0.85; umbrales ≥0.55 provocaban rechazos falsos. Ajustar solo con evidencia de `scripts/eval_rag_recall.py`.
- **Preproceso:** `strip()` únicamente; sin lowercasing (montos COP/USD y nombres de platos deben sobrevivir).

---

## 4. Módulos

| Responsabilidad | Ruta |
| --------------- | ---- |
| Chunking + indexación | `data/process/rag.py` |
| Recuperación + generación | `data/pipelines/rag.py` |
| HTTP | `services/knowledge/router.py` → `POST /knowledge/query` |
| UI | `uis/backoffice/src/app/knowledge/page.tsx` |
| Tests | `tests/pipelines/test_rag.py` |
| Eval Recall@3 | `data/eval/test-queries.json` + `scripts/eval_rag_recall.py` |

---

## 5. Cómo operar

```bash
# Indexar (local path Qdrant si no hay servidor)
uv run python -m data.process.rag

# Eval retrieval
uv run python scripts/eval_rag_recall.py

# Tests
uv run pytest tests/pipelines/test_rag.py -q
```

Docker Compose incluye el servicio `qdrant` (`:6333`). En Compose el backend usa `QDRANT_URL=http://qdrant:6333`.
