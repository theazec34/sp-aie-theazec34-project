"use client";

import { FormEvent, useState } from "react";
import AuthenticatedShell from "../../components/AuthenticatedShell";
import { apiFetch } from "../../lib/api";
import { getApiBaseUrl } from "../../lib/auth";
import { friendlyCatch, readApiError } from "../../lib/errors";

type QueryResponse = {
  answer: string;
};

/** Primera carga: FastEmbed puede bajar el modelo; luego LLM 4Geeks. */
const QUERY_TIMEOUT_MS = 120_000;
const REINDEX_TIMEOUT_MS = 180_000;

export default function KnowledgePage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) {
      setError("Escribe una pregunta.");
      setAnswer("");
      return;
    }
    setLoading(true);
    setError("");
    setInfo("");
    setAnswer("");
    try {
      const response = await apiFetch("/knowledge/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
        signal: AbortSignal.timeout(QUERY_TIMEOUT_MS),
      });
      if (!response.ok) {
        const parsed = await readApiError(response);
        throw new Error(parsed.message);
      }
      const data = (await response.json()) as QueryResponse;
      if (!data.answer?.trim()) {
        throw new Error("La API no devolvió una respuesta generada.");
      }
      setAnswer(data.answer);
    } catch (err) {
      const name = err instanceof Error ? err.name : "";
      if (name === "TimeoutError" || name === "AbortError") {
        setError(
          "BrasAI no respondió a tiempo (120s). Suele ser: 1) colección Qdrant " +
            "sin indexar → pulsa «Reindexar manuales», 2) modelo LLM lento/incorrecto " +
            "en GENERATION_MODEL_ID, 3) primera descarga de FastEmbed. " +
            "Revisa: docker compose logs backend | tail -80",
        );
      } else {
        setError(friendlyCatch(err, getApiBaseUrl()));
      }
      setAnswer("");
    } finally {
      setLoading(false);
    }
  }

  async function onReindex() {
    setReindexing(true);
    setError("");
    setInfo("Indexando manuales en Qdrant (puede tardar 1–3 min)…");
    try {
      const response = await apiFetch("/knowledge/reindex", {
        method: "POST",
        signal: AbortSignal.timeout(REINDEX_TIMEOUT_MS),
      });
      if (!response.ok) {
        const parsed = await readApiError(response);
        throw new Error(parsed.message);
      }
      const data = (await response.json()) as {
        chunks_indexed?: number;
        collection?: string;
      };
      setInfo(
        `Listo: ${data.chunks_indexed ?? "?"} fragmentos en «${data.collection ?? "brasaland_knowledge"}». Ya puedes preguntar.`,
      );
    } catch (err) {
      setInfo("");
      setError(friendlyCatch(err, getApiBaseUrl()));
    } finally {
      setReindexing(false);
    }
  }

  return (
    <AuthenticatedShell active="knowledge">
      <header className="bo-topbar">
        <div>
          <p className="bo-kicker">Operaciones · Marketing</p>
          <h1>BrasAI</h1>
          <p className="bo-soft">
            Responde solo con los <strong>manuales oficiales</strong> indexados
            (RAG). No consulta reservas, candidaturas ni stock en vivo — eso es
            el <strong>Agente soporte</strong>.
          </p>
        </div>
        <button
          type="button"
          className="bo-btn bo-btn-small"
          disabled={reindexing || loading}
          onClick={() => void onReindex()}
        >
          {reindexing ? "Indexando…" : "Reindexar manuales"}
        </button>
      </header>

      <section className="bo-panel">
        <h3>Qué puede responder</h3>
        <ul className="bo-soft" style={{ margin: "0.5rem 0 0", paddingLeft: "1.2rem" }}>
          <li>Brasa Points / niveles de fidelización (Plata, Oro, Platino)</li>
          <li>Alérgenos y carta (p. ej. Costilla BBQ, paellas)</li>
          <li>Protocolo de desperdicio y merma</li>
          <li>Procedimiento de pedidos a proveedores (manual, no datos en vivo)</li>
        </ul>
      </section>

      <section className="bo-panel">
        <form className="bo-form" onSubmit={onSubmit}>
          <label htmlFor="knowledge-question">Pregunta</label>
          <textarea
            id="knowledge-question"
            className="bo-field"
            rows={4}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading || reindexing}
            placeholder="Ej. ¿Qué alérgenos tiene la Costilla BBQ?"
          />
          <button
            type="submit"
            className="bo-btn bo-btn-primary"
            disabled={loading || reindexing}
          >
            {loading ? "Consultando…" : "Preguntar a BrasAI"}
          </button>
        </form>
      </section>

      {info ? (
        <section className="bo-panel" aria-live="polite">
          <p className="bo-soft">{info}</p>
        </section>
      ) : null}

      {error ? (
        <section className="bo-panel" role="alert">
          <h3>Error</h3>
          <p className="bo-soft">{error}</p>
        </section>
      ) : null}

      {loading ? (
        <section className="bo-panel" aria-live="polite">
          <p className="bo-soft">
            BrasAI está generando la respuesta (embeddings + LLM; la primera
            vez puede tardar más de un minuto)…
          </p>
        </section>
      ) : null}

      {!loading && answer ? (
        <section className="bo-panel" aria-live="polite">
          <h3>Respuesta</h3>
          <p style={{ whiteSpace: "pre-wrap", lineHeight: 1.55 }}>{answer}</p>
        </section>
      ) : null}
    </AuthenticatedShell>
  );
}
