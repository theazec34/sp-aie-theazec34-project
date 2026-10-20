"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import AuthenticatedShell from "../../components/AuthenticatedShell";
import {
  connectAgentChat,
  type AgentChatController,
  type ChatMessage,
} from "../../lib/agentChatWs";

type Conn = "connecting" | "open" | "reconnecting" | "closed";

function connLabel(s: Conn): string {
  switch (s) {
    case "open":
      return "En vivo";
    case "connecting":
      return "Conectando…";
    case "reconnecting":
      return "Reconectando…";
    default:
      return "Desconectado";
  }
}

export default function AgentChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [conn, setConn] = useState<Conn>("connecting");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [locationId, setLocationId] = useState("miami_doral");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ctrlRef = useRef<AgentChatController | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const ctrl = connectAgentChat(
      {
        onConnectionChange: setConn,
        onError: setError,
        onSnapshot: (data) => {
          setSessionId(data.session_id);
          setMessages(data.messages || []);
          setStreaming(false);
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
      { locationId },
    );
    ctrlRef.current = ctrl;
    return () => ctrl.stop();
  }, [locationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    setError(null);
    setInput("");
    // Si el agente está respondiendo, enviar interrumpe de verdad en backend
    ctrlRef.current?.sendUserMessage(text);
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
            Conversación en vivo: la respuesta llega token a token y puedes
            interrumpir si el agente se desvía. Sesión:{" "}
            <code>{sessionId || "…"}</code>
          </p>
        </div>
        <span className={`bo-sse-status bo-sse-status-${conn}`}>{connLabel(conn)}</span>
      </div>

      <div className="bo-card" style={{ marginBottom: "1rem" }}>
        <label className="bo-field">
          Local / sede
          <input
            value={locationId}
            onChange={(e) => setLocationId(e.target.value)}
            placeholder="miami_doral"
          />
        </label>
      </div>

      {error ? (
        <p className="bo-alert bo-alert-error" role="alert">
          {error}
        </p>
      ) : null}

      <section className="bo-card bo-agent-chat-log" aria-live="polite">
        {messages.length === 0 ? (
          <p className="bo-muted">Escribe una pregunta operativa del local.</p>
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

      <form onSubmit={onSubmit} className="bo-card bo-agent-chat-form">
        <textarea
          rows={3}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            streaming
              ? "Escribe para interrumpir y redirigir…"
              : "Ej. ¿Horario de proveedores en Miami Doral?"
          }
        />
        <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
          <button type="submit" className="bo-btn bo-btn-primary" disabled={!input.trim()}>
            {streaming ? "Interrumpir y enviar" : "Enviar"}
          </button>
          {streaming ? (
            <button type="button" className="bo-btn" onClick={onStop}>
              Detener generación
            </button>
          ) : null}
        </div>
      </form>
    </AuthenticatedShell>
  );
}
