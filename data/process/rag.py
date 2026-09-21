"""Brasaland RAG indexing — Phase 1.

Public API:
  - ``embed(text) -> list[float]`` — dedicated embedding model only
  - ``setup()`` — load corpus, semantic chunk, embed, upsert to Qdrant

Idempotency: deterministic UUID5 point IDs + upsert (re-runs do not duplicate).
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Fixed namespace for deterministic point IDs — do not change after first index.
BRASALAND_RAG_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-4789-a012-3456789abcde")

COMPANY = "brasaland"
COLLECTION_NAME = "brasaland_knowledge"
LANGUAGE = "es"
MAX_SECTION_CHARS = 1000
MIN_CHUNKS_PER_DOC = 3

SOURCE_DOCUMENT_BY_FILE = {
    "brasaland-loyalty-program.es.md": "loyalty-program",
    "brasaland-waste-protocol.es.md": "waste-protocol",
    "brasaland-menu-allergens.es.md": "menu-allergens",
    "brasaland-supplier-ordering.es.md": "supplier-ordering",
}

# Flat manuals (ES) — section cues when ## headings are absent.
_SECTION_START_RE = re.compile(
    r"^(?P<title>"
    r"Niveles del programa|"
    r"Preguntas frecuentes de clientes|"
    r"Platos principales y sus alérgenos declarados|"
    r"Protocolo ante alergias reportadas por el cliente|"
    r"Procedimiento diario|"
    r"Causas comunes de desperdicio aceptadas sin nota adicional|"
    r"Causas que requieren escalamiento a Felipe Guerrero directamente|"
    r"Meta operativa|"
    r"Categorías de proveedores y frecuencia de pedido|"
    r"Regla de stock mínimo"
    r"):\s*(?P<rest>.*)$",
    re.IGNORECASE,
)

_HEADING_RE = re.compile(r"^(#{1,3})\s+(?P<title>.+?)\s*$")


@dataclass
class Chunk:
    source_document: str
    section: str
    chunk_index: int
    text: str
    language: str = LANGUAGE
    company: str = COMPANY

    def point_id(self) -> str:
        key = f"{self.source_document}:{self.chunk_index}:{self.section}"
        return str(uuid.uuid5(BRASALAND_RAG_NAMESPACE, key))

    def payload(self) -> dict[str, Any]:
        return {
            "company": self.company,
            "source_document": self.source_document,
            "section": self.section,
            "language": self.language,
            "chunk_index": self.chunk_index,
            "text": self.text,
        }


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    here = Path(__file__).resolve()
    for root in [here.parent, *here.parents]:
        candidate = root / ".env"
        if candidate.exists():
            load_dotenv(candidate)
            return


def resolve_knowledge_base_dir() -> Path:
    """Corpus path: docs/company-knowledge-base/ (CONTEXT §2)."""
    override = os.getenv("BRASALAND_KNOWLEDGE_BASE_DIR", "").strip()
    if override:
        path = Path(override)
        if path.is_dir():
            return path.resolve()
        raise FileNotFoundError(
            f"BRASALAND_KNOWLEDGE_BASE_DIR is set but not a directory: {override}"
        )

    docker_path = Path("/app/docs/company-knowledge-base")
    if docker_path.is_dir():
        return docker_path.resolve()

    repo_root = Path(__file__).resolve().parents[2]
    local_path = repo_root / "docs" / "company-knowledge-base"
    if local_path.is_dir():
        return local_path.resolve()

    raise FileNotFoundError(
        "Could not resolve docs/company-knowledge-base/. "
        "Copy CONTEXT source manuals there or set BRASALAND_KNOWLEDGE_BASE_DIR."
    )


def collection_name() -> str:
    return os.getenv("QDRANT_COLLECTION", COLLECTION_NAME).strip() or COLLECTION_NAME


def _qdrant_url() -> str:
    return os.getenv("QDRANT_URL", "").strip()


def _qdrant_path() -> str:
    """Local embedded storage when no Qdrant server URL is set."""
    default = Path(__file__).resolve().parents[2] / ".qdrant_storage"
    return os.getenv("QDRANT_PATH", str(default)).strip() or str(default)


def get_qdrant_client():
    """Qdrant client: URL server, else local path (no Docker required)."""
    from qdrant_client import QdrantClient

    url = _qdrant_url()
    if url:
        return QdrantClient(url=url, timeout=60)
    if os.getenv("QDRANT_MEMORY", "").strip().lower() in {"1", "true", "yes"}:
        return QdrantClient(":memory:")
    path = _qdrant_path()
    Path(path).mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=path)


def _embedding_provider() -> str:
    """openai (4Geeks OpenAI-compatible) | fastembed (free local default)."""
    explicit = os.getenv("EMBEDDING_PROVIDER", "").strip().lower()
    if explicit:
        return explicit
    if os.getenv("EMBEDDING_BASE_URL", "").strip() and os.getenv(
        "EMBEDDING_MODEL_ID", ""
    ).strip():
        return "openai"
    return "fastembed"


def _embedding_settings() -> tuple[str, str, str]:
    base_url = os.getenv("EMBEDDING_BASE_URL", "").strip()
    api_key = os.getenv("EMBEDDING_API_KEY", "").strip() or "not-needed"
    model_id = os.getenv("EMBEDDING_MODEL_ID", "").strip()
    generation_id = os.getenv("GENERATION_MODEL_ID", "").strip()
    if generation_id and model_id and generation_id == model_id:
        raise RuntimeError(
            "EMBEDDING_MODEL_ID must differ from GENERATION_MODEL_ID"
        )
    return base_url, api_key, model_id


def _fastembed_model_name() -> str:
    # Multilingual — corpus is Spanish. Distinct from any generation LLM.
    return (
        os.getenv("FASTEMBED_MODEL", "").strip()
        or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )


_fastembed_model = None


def _get_fastembed():
    global _fastembed_model
    if _fastembed_model is None:
        from fastembed import TextEmbedding

        _fastembed_model = TextEmbedding(model_name=_fastembed_model_name())
    return _fastembed_model


def embed(text: str) -> list[float]:
    """Generate a vector with the dedicated embedding model (not generation)."""
    if not text or not text.strip():
        raise ValueError("embed() requires non-empty text")
    cleaned = text.strip()
    provider = _embedding_provider()

    if provider == "openai":
        from openai import OpenAI

        base_url, api_key, model_id = _embedding_settings()
        if not base_url or not model_id:
            raise RuntimeError(
                "EMBEDDING_BASE_URL and EMBEDDING_MODEL_ID required for "
                "EMBEDDING_PROVIDER=openai (4Geeks student portal)."
            )
        client = OpenAI(base_url=base_url, api_key=api_key)
        response = client.embeddings.create(model=model_id, input=cleaned)
        return list(response.data[0].embedding)

    if provider == "fastembed":
        model = _get_fastembed()
        vectors = list(model.embed([cleaned]))
        return [float(x) for x in vectors[0].tolist()]

    raise RuntimeError(f"Unknown EMBEDDING_PROVIDER={provider!r}")


def embedding_dimension() -> int:
    """Probe vector size for collection creation."""
    return len(embed("dimension probe"))


def _source_document_from_filename(filename: str) -> str:
    if filename in SOURCE_DOCUMENT_BY_FILE:
        return SOURCE_DOCUMENT_BY_FILE[filename]
    stem = filename
    for suffix in (".es.md", ".en.md", ".md"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    if stem.startswith("brasaland-"):
        stem = stem[len("brasaland-") :]
    return stem or filename


def _split_oversized(section: str, body: str) -> list[tuple[str, str]]:
    """Split long sections on blank-line paragraphs — never mid-sentence."""
    body = body.strip()
    if len(body) <= MAX_SECTION_CHARS:
        return [(section, body)]

    paragraphs = re.split(r"\n\s*\n", body)
    chunks: list[tuple[str, str]] = []
    buf: list[str] = []
    buf_len = 0
    part = 1
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        extra = len(para) + (2 if buf else 0)
        if buf and buf_len + extra > MAX_SECTION_CHARS:
            label = section if part == 1 else f"{section} ({part})"
            chunks.append((label, "\n\n".join(buf).strip()))
            part += 1
            buf = [para]
            buf_len = len(para)
        else:
            buf.append(para)
            buf_len += extra
    if buf:
        label = section if part == 1 else f"{section} ({part})"
        chunks.append((label, "\n\n".join(buf).strip()))
    return chunks


def _ensure_min_chunks(
    sections: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Guarantee ≥ MIN_CHUNKS_PER_DOC by splitting largest chunks on lines."""
    out = list(sections)
    while len(out) < MIN_CHUNKS_PER_DOC:
        # Find largest chunk with ≥2 lines
        idx = max(range(len(out)), key=lambda i: len(out[i][1]))
        title, body = out[idx]
        lines = [ln for ln in body.splitlines() if ln.strip()]
        if len(lines) < 2:
            break
        mid = max(1, len(lines) // 2)
        left = "\n".join(lines[:mid]).strip()
        right = "\n".join(lines[mid:]).strip()
        if not left or not right:
            break
        out[idx] = (f"{title} (a)", left)
        out.insert(idx + 1, (f"{title} (b)", right))
    return out


def chunk_document(filename: str, content: str) -> list[Chunk]:
    """Semantic chunking: headings / labeled sections, never mid-rule cuts."""
    source = _source_document_from_filename(filename)
    lines = content.replace("\r\n", "\n").split("\n")
    title = Path(filename).stem
    # First non-empty line as doc title if markdown H1
    for line in lines:
        m = _HEADING_RE.match(line.strip())
        if m and len(m.group(1)) == 1:
            title = m.group("title").strip()
            break
        if line.strip().startswith("# "):
            title = line.strip()[2:].strip()
            break

    sections: list[tuple[str, str]] = []
    current_title = title
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_lines, current_title
        body = "\n".join(current_lines).strip()
        if body:
            sections.extend(_split_oversized(current_title, body))
        current_lines = []

    for raw in lines:
        line = raw.rstrip()
        heading = _HEADING_RE.match(line.strip())
        section_cue = _SECTION_START_RE.match(line.strip())
        if heading:
            flush()
            current_title = heading.group("title").strip()
            continue
        if section_cue:
            flush()
            current_title = section_cue.group("title").strip()
            rest = (section_cue.group("rest") or "").strip()
            if rest:
                current_lines.append(rest)
            continue
        current_lines.append(line)
    flush()

    if not sections:
        sections = [(title, content.strip())]

    sections = _ensure_min_chunks(sections)
    chunks: list[Chunk] = []
    for i, (section, text) in enumerate(sections):
        if not text.strip():
            continue
        chunks.append(
            Chunk(
                source_document=source,
                section=section,
                chunk_index=i,
                text=text.strip(),
            )
        )
    return chunks


def load_corpus_chunks(knowledge_dir: Path | None = None) -> list[Chunk]:
    root = knowledge_dir or resolve_knowledge_base_dir()
    chunks: list[Chunk] = []
    files = sorted(root.glob("brasaland-*.es.md"))
    if not files:
        files = sorted(root.glob("*.md"))
    missing = [
        name
        for name in SOURCE_DOCUMENT_BY_FILE
        if not (root / name).exists()
    ]
    if missing:
        logger.warning("Missing expected source files: %s", missing)
    for path in files:
        text = path.read_text(encoding="utf-8")
        doc_chunks = chunk_document(path.name, text)
        if len(doc_chunks) < MIN_CHUNKS_PER_DOC:
            raise ValueError(
                f"{path.name} produced {len(doc_chunks)} chunks; "
                f"need ≥ {MIN_CHUNKS_PER_DOC}"
            )
        chunks.extend(doc_chunks)
    return chunks


def _ensure_collection(client, vector_size: int) -> None:
    from qdrant_client.http import models as qmodels

    name = collection_name()
    existing = {c.name for c in client.get_collections().collections}
    if name in existing:
        info = client.get_collection(name)
        # Recreate if dimension mismatch (dev clear-and-reload for config drift)
        current_size = info.config.params.vectors.size  # type: ignore[union-attr]
        if current_size != vector_size:
            logger.warning(
                "Recreating collection %s (size %s → %s)",
                name,
                current_size,
                vector_size,
            )
            client.delete_collection(name)
        else:
            return
    client.create_collection(
        collection_name=name,
        vectors_config=qmodels.VectorParams(
            size=vector_size,
            distance=qmodels.Distance.COSINE,
        ),
    )


def setup(*, recreate: bool = False) -> dict[str, Any]:
    """Index ``docs/company-knowledge-base/`` into Qdrant ``brasaland_knowledge``.

    Idempotent via UUID5 point IDs + upsert. Optional ``recreate`` wipes the
    collection first (clear-and-reload).
    """
    _load_env()
    from qdrant_client.http import models as qmodels

    chunks = load_corpus_chunks()
    if not chunks:
        raise RuntimeError("No chunks produced from knowledge base")

    client = get_qdrant_client()
    name = collection_name()
    dim = embedding_dimension()

    if recreate and name in {c.name for c in client.get_collections().collections}:
        client.delete_collection(name)

    _ensure_collection(client, dim)

    points = []
    for chunk in chunks:
        vector = embed(chunk.text)
        points.append(
            qmodels.PointStruct(
                id=chunk.point_id(),
                vector=vector,
                payload=chunk.payload(),
            )
        )

    client.upsert(collection_name=name, points=points)
    by_source: dict[str, int] = {}
    for chunk in chunks:
        by_source[chunk.source_document] = (
            by_source.get(chunk.source_document, 0) + 1
        )

    result = {
        "collection": name,
        "chunks_indexed": len(chunks),
        "vector_size": dim,
        "embedding_provider": _embedding_provider(),
        "embedding_model": (
            _fastembed_model_name()
            if _embedding_provider() == "fastembed"
            else os.getenv("EMBEDDING_MODEL_ID", "")
        ),
        "idempotency": "uuid5 upsert",
        "chunks_by_source": by_source,
    }
    logger.info("setup complete: %s", result)
    return result


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Index Brasaland knowledge base")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete collection before upsert (clear-and-reload)",
    )
    args = parser.parse_args(argv)
    result = setup(recreate=args.recreate)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
