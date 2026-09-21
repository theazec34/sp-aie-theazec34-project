"use client";

import { FormEvent, useState } from "react";
import AuthenticatedShell from "../../components/AuthenticatedShell";
import { apiFetch } from "../../lib/api";
import { getApiBaseUrl } from "../../lib/auth";
import { friendlyCatch, readApiError } from "../../lib/errors";

type QueryResponse = {
  answer: string;
};

export default function KnowledgePage() {
  const [question, setQuestion] = useState(
    "¿Cuántos puntos necesito para el nivel Oro?",
  );
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
    setAnswer("");
    try {
      const response = await apiFetch("/knowledge/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
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
      setError(friendlyCatch(err, getApiBaseUrl()));
      setAnswer("");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthenticatedShell active="knowledge">
      <header className="bo-topbar">
        <div>
          <p className="bo-kicker">Operaciones · Marketing</p>
          <h1>Base de conocimiento</h1>
          <p className="bo-soft">
            Preguntas sobre Brasa Points, desperdicio, alérgenos y pedidos a
            proveedores — respuestas generadas desde los manuales oficiales.
          </p>
        </div>
      </header>

      <section className="bo-panel">
        <form className="bo-form" onSubmit={onSubmit}>
          <label htmlFor="knowledge-question">Pregunta</label>
          <textarea
            id="knowledge-question"
            className="bo-input"
            rows={4}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
            placeholder="Ej. ¿La Costilla BBQ tiene alérgenos?"
          />
          <button
            type="submit"
            className="bo-btn bo-btn-primary"
            disabled={loading}
          >
            {loading ? "Consultando…" : "Preguntar"}
          </button>
        </form>
      </section>

      {error ? (
        <section className="bo-panel" role="alert">
          <h3>Error</h3>
          <p className="bo-soft">{error}</p>
        </section>
      ) : null}

      {loading ? (
        <section className="bo-panel" aria-live="polite">
          <p className="bo-soft">Generando respuesta desde la base de conocimiento…</p>
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
