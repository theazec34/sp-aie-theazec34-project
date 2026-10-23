"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import AuthenticatedShell from "../../components/AuthenticatedShell";
import { apiFetch } from "../../lib/api";
import { getApiBaseUrl } from "../../lib/auth";
import { friendlyCatch, readApiError } from "../../lib/errors";
import { INCIDENT_BRANCHES, labelFor } from "../../lib/incidents";
import {
  connectAgentChat,
  type AgentChatController,
  type ChatMessage,
} from "../../lib/agentChatWs";

type Conn = "connecting" | "open" | "reconnecting" | "closed";

function connLabel(s: Conn): string {
  switch (s) {
    case "open":
      return "En vivo (WebSocket)";
    case "connecting":
      return "Conectando…";
    case "reconnecting":
      return "HTTP (WS caído)";
    default:
      return "HTTP";
  }
}

export default function AgentChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [conn, setConn] = useState<Conn>("connecting");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [locationId, setLocationId] = useState("miami_doral");
  const [activeLocationId, setActiveLocationId] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ctrlRef = useRef<AgentChatController | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const connRef = useRef<Conn>("connecting");
  const prevLocationRef = useRef<string | null>(null);

  useEffect(() => {
    connRef.current = conn;
  }, [conn]);

  useEffect(() => {
    // Al cambiar sede: sesión nueva (no rehidratar chat de otra local).
    const sedeChanged =
      prevLocationRef.current !== null && prevLocationRef.current !== locationId;
    prevLocationRef.current = locationId;
    if (sedeChanged) {
      setMessages([]);
      setSessionId(null);
      setActiveLocationId(null);
      setStreaming(false);
      setError(null);
    }

    const ctrl = connectAgentChat(
      {
        onConnectionChange: setConn,
        onError: (detail) => {
          // No bloquear el chat: modo HTTP cubre el WS caído en Codespaces.
          if (detail) setError(detail);
        },
        onSnapshot: (data) => {
          setSessionId(data.session_id);
          setActiveLocationId(data.location_id ?? locationId);
          setMessages(data.messages || []);
          setStreaming(false);
          setError(null);
        },
        onUserMessage: (data) => {
          setMessages((prev) => {
            if (data.message_id && prev.some((m) => m.message_id === data.message_id)) {
              return prev;
            }
            return [
              ...prev,
              {
                message_id: data.message_id || `local_${Date.now()}`,
                role: "user",
                content: data.text,
                status: "complete",
              },
            ];
          });
        },
        onTokenChunk: (data) => {
          setStreaming(true);
          setMessages((prev) => {
            const idx = prev.findIndex((m) => m.message_id === data.message_id);
            if (idx >= 0) {
              const next = [...prev];
              next[idx] = {
                ...next[idx],
                content: next[idx].content + data.token,
                status: "streaming",
              };
              return next;
            }
            return [
              ...prev,
              {
                message_id: data.message_id,
                role: "assistant",
                content: data.token,
                status: "streaming",
              },
            ];
          });
        },
        onInterrupted: (data) => {
          setStreaming(false);
          setMessages((prev) =>
            prev.map((m) =>
              m.message_id === data.message_id
                ? { ...m, status: "interrupted" as const }
                : m,
            ),
          );
        },
        onCompleted: (data) => {
          setStreaming(false);
          setMessages((prev) =>
            prev.map((m) =>
              m.message_id === data.message_id
                ? { ...m, status: "complete" as const }
                : m,
            ),
          );
        },
      },
      { locationId, freshSession: sedeChanged },
    );
    ctrlRef.current = ctrl;
    return () => ctrl.stop();
  }, [locationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendViaHttp(text: string) {
    const userId = `http_u_${Date.now()}`;
    const asstId = `http_a_${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { message_id: userId, role: "user", content: text, status: "complete" },
      {
        message_id: asstId,
        role: "assistant",
        content: "Consultando…",
        status: "streaming",
      },
    ]);
    setStreaming(true);
    try {
      const response = await apiFetch("/agent/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: text,
          session_id: sessionId || undefined,
          location_id: locationId || undefined,
        }),
        signal: AbortSignal.timeout(90_000),
      });
      if (!response.ok) {
        const parsed = await readApiError(response);
        throw new Error(parsed.message);
      }
      const data = (await response.json()) as {
        answer?: string;
        session_id?: string;
      };
      if (data.session_id) setSessionId(data.session_id);
      setMessages((prev) =>
        prev.map((m) =>
          m.message_id === asstId
            ? {
                ...m,
                content: data.answer?.trim() || "Sin respuesta del agente.",
                status: "complete" as const,
              }
            : m,
        ),
      );
      setError(null);
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.message_id === asstId
            ? {
                ...m,
                content: friendlyCatch(err, getApiBaseUrl()),
                status: "interrupted" as const,
              }
            : m,
        ),
      );
      setError(friendlyCatch(err, getApiBaseUrl()));
    } finally {
      setStreaming(false);
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || streaming) return;
    setError(null);
    setInput("");
    if (connRef.current === "open" && ctrlRef.current) {
      ctrlRef.current.sendUserMessage(text);
      return;
    }
    await sendViaHttp(text);
  }

  function onStop() {
    ctrlRef.current?.interrupt();
  }

  return (
    <AuthenticatedShell active="agent">
      <div className="bo-rfp-header">
        <div>
          <p className="bo-kicker">Operaciones · Felipe Guerrero</p>
          <h1>Agente de soporte para encargados</h1>
          <p className="bo-muted">
            Datos operativos en vivo: proveedores (€), existencias, entradas/
            salidas e historial de inventario, e incidencias. Sesión:{" "}
            <code>{sessionId || "…"}</code>
          </p>
        </div>
        <span
          className={`bo-sse-status bo-sse-status-${conn}`}
          title={
            conn === "open"
              ? "Canal WebSocket abierto: el chat habla en directo con el API :8000"
              : "Sin WebSocket: las preguntas van por HTTP (POST /agent/query)"
          }
        >
          {connLabel(conn)}
        </span>
      </div>

      {conn === "open" ? (
        <p className="bo-soft" style={{ marginBottom: "0.75rem" }}>
          Canal en vivo: la etiqueta verde «En vivo (WebSocket)» confirma que el
          chat está conectado al API. Si cambia a «HTTP» o «Conectando…», no hay
          WS (en Codespaces pon el puerto <strong>8000 en Public</strong>).
        </p>
      ) : (
        <p className="bo-soft" style={{ marginBottom: "0.75rem" }}>
          WebSocket no conectado (en Codespaces pon el puerto <strong>8000 en
          Public</strong>). Mientras tanto el chat usa{" "}
          <code>POST /agent/query</code> vía <code>/api-backend</code> — sigue
          filtrando por la sede elegida abajo.
        </p>
      )}

      <div className="bo-card" style={{ marginBottom: "1rem" }}>
        <label className="bo-field" htmlFor="agent-location">
          Local / sede
          <select
            id="agent-location"
            value={locationId}
            onChange={(e) => setLocationId(e.target.value)}
          >
            {INCIDENT_BRANCHES.map((b) => (
              <option key={b.value} value={b.value}>
                {b.label}
              </option>
            ))}
          </select>
        </label>
        <p className="bo-muted" style={{ marginTop: "0.5rem", marginBottom: 0 }}>
          Sede activa en la sesión:{" "}
          <strong>
            {labelFor(INCIDENT_BRANCHES, activeLocationId || locationId)}
          </strong>{" "}
          (<code>{activeLocationId || locationId}</code>). Al cambiar de local se
          abre un chat nuevo con ese filtro.
        </p>
      </div>

      {error ? (
        <p className="bo-alert bo-alert-error" role="alert">
          {error}
        </p>
      ) : null}

      <section className="bo-card bo-agent-chat-log" aria-live="polite">
        {messages.length === 0 ? (
          <div className="bo-muted">
            <p>Prueba preguntas como:</p>
            <ul style={{ margin: "0.35rem 0 0", paddingLeft: "1.2rem" }}>
              <li>¿Cuál es el proveedor con la tarifa más alta en €?</li>
              <li>¿Qué reservas tengo hoy en esta sede?</li>
              <li>¿Cuántas candidaturas hay?</li>
              <li>¿Qué stock tenemos ahora de cada ingrediente?</li>
              <li>¿Qué proveedor nos ha enviado más kg?</li>
            </ul>
            <p style={{ marginTop: "0.5rem" }}>
              Tras <code>seed_demo_ops</code> hay proveedores/reservas/candidaturas
              por sede (hoy y mañana). Reservas web y Candidaturas en el panel.
            </p>
          </div>
        ) : null}
        {messages.map((m) => (
          <article
            key={m.message_id}
            className={`bo-agent-bubble bo-agent-bubble-${m.role}${
              m.status === "interrupted" ? " bo-agent-bubble-interrupted" : ""
            }`}
          >
            <header>
              <strong>{m.role === "user" ? "Tú" : "Agente"}</strong>
              {m.status === "interrupted" ? (
                <span className="bo-rfp-fresh-badge">Interrumpido</span>
              ) : null}
              {m.status === "streaming" ? (
                <span className="bo-rfp-fresh-badge">Escribiendo…</span>
              ) : null}
            </header>
            <p style={{ whiteSpace: "pre-wrap", margin: "0.35rem 0 0" }}>{m.content}</p>
          </article>
        ))}
        <div ref={bottomRef} />
      </section>

      <form onSubmit={(e) => void onSubmit(e)} className="bo-card bo-agent-chat-form">
        <textarea
          rows={3}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            streaming
              ? "Espera a que termine la respuesta…"
              : "Ej. ¿Cuál es el mayor proveedor en € y cuántos kg hemos recibido?"
          }
        />
        <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
          <button
            type="submit"
            className="bo-btn bo-btn-primary"
            disabled={!input.trim() || streaming}
          >
            {streaming ? "Consultando…" : "Enviar"}
          </button>
          {streaming && conn === "open" ? (
            <button type="button" className="bo-btn" onClick={onStop}>
              Detener generación
            </button>
          ) : null}
        </div>
      </form>
    </AuthenticatedShell>
  );
}
