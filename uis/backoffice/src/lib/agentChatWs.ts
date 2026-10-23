/**
 * Cliente WebSocket del Manager support agent.
 * Auth: ?token= (browsers no envían Authorization en el handshake WS).
 * Reconexión con backoff + mismo session_id para rehidratar.
 */

import { getDirectApiBaseUrl, getToken } from "./auth";

export type ChatMessage = {
  message_id: string;
  role: "user" | "assistant";
  content: string;
  status: "complete" | "streaming" | "interrupted";
  created_at?: string;
};

export type AgentChatHandlers = {
  onSnapshot?: (data: {
    session_id: string;
    messages: ChatMessage[];
    status?: string;
    agent_id?: string;
    location_id?: string | null;
  }) => void;
  onTokenChunk?: (data: {
    session_id: string;
    message_id: string;
    token: string;
    sequence: number;
  }) => void;
  onUserMessage?: (data: { session_id: string; message_id?: string; text: string }) => void;
  onInterrupted?: (data: {
    session_id: string;
    message_id: string;
    status: string;
  }) => void;
  onCompleted?: (data: { session_id: string; message_id: string }) => void;
  onConnectionChange?: (
    state: "connecting" | "open" | "reconnecting" | "closed",
  ) => void;
  onError?: (detail: string) => void;
};

const SESSION_KEY = "brasaland_agent_chat_session_id";

export function getStoredSessionId(): string | null {
  try {
    return sessionStorage.getItem(SESSION_KEY);
  } catch {
    return null;
  }
}

export function setStoredSessionId(id: string) {
  try {
    sessionStorage.setItem(SESSION_KEY, id);
  } catch {
    /* ignore */
  }
}

function wsBaseUrl(): string {
  // WS no pasa por el rewrite de Next; usar origen absoluto de la API.
  const http = getDirectApiBaseUrl().replace(/\/$/, "");
  if (http.startsWith("https://")) return `wss://${http.slice("https://".length)}`;
  if (http.startsWith("http://")) return `ws://${http.slice("http://".length)}`;
  return `ws://${http}`;
}

export type AgentChatController = {
  stop: () => void;
  sendUserMessage: (text: string) => void;
  interrupt: (newInput?: string) => void;
  getSessionId: () => string | null;
};

export function clearStoredSessionId() {
  try {
    sessionStorage.removeItem(SESSION_KEY);
  } catch {
    /* ignore */
  }
}

export function connectAgentChat(
  handlers: AgentChatHandlers,
  opts?: { locationId?: string; sessionId?: string | null; freshSession?: boolean },
): AgentChatController {
  let stopped = false;
  let attempt = 0;
  let socket: WebSocket | null = null;
  // freshSession / sessionId:null → no reutilizar chat de otra sede
  if (opts?.freshSession) {
    clearStoredSessionId();
  }
  let sessionId: string | null =
    opts?.freshSession || opts?.sessionId === null
      ? null
      : (opts?.sessionId ?? getStoredSessionId());
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  const backoffMs = () => Math.min(30_000, 1000 * 2 ** Math.min(attempt, 5));

  function send(frame: { event: string; data: Record<string, unknown> }) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(frame));
    }
  }

  function scheduleReconnect() {
    if (stopped) return;
    handlers.onConnectionChange?.("reconnecting");
    if (reconnectTimer) clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(() => {
      attempt += 1;
      open();
    }, backoffMs());
  }

  function open() {
    if (stopped) return;
    const token = getToken();
    if (!token) {
      scheduleReconnect();
      return;
    }
    handlers.onConnectionChange?.(attempt === 0 ? "connecting" : "reconnecting");

    const params = new URLSearchParams({ token });
    if (sessionId) params.set("session_id", sessionId);
    if (opts?.locationId) params.set("location_id", opts.locationId);

    const url = `${wsBaseUrl()}/agent/chat/ws?${params.toString()}`;
    socket = new WebSocket(url);

    socket.onopen = () => {
      attempt = 0;
      handlers.onConnectionChange?.("open");
    };

    socket.onmessage = (ev) => {
      let frame: { event?: string; data?: Record<string, unknown> };
      try {
        frame = JSON.parse(String(ev.data));
      } catch {
        return;
      }
      const data = (frame.data || {}) as Record<string, unknown>;
      switch (frame.event) {
        case "session_snapshot": {
          const sid = String(data.session_id || "");
          if (sid) {
            sessionId = sid;
            setStoredSessionId(sid);
          }
          handlers.onSnapshot?.({
            session_id: sid,
            messages: (data.messages as ChatMessage[]) || [],
            status: data.status as string | undefined,
            agent_id: data.agent_id as string | undefined,
            location_id: (data.location_id as string | null) ?? null,
          });
          break;
        }
        case "token_chunk":
          handlers.onTokenChunk?.({
            session_id: String(data.session_id || ""),
            message_id: String(data.message_id || ""),
            token: String(data.token || ""),
            sequence: Number(data.sequence ?? 0),
          });
          break;
        case "user_message":
          handlers.onUserMessage?.({
            session_id: String(data.session_id || ""),
            message_id: data.message_id as string | undefined,
            text: String(data.text || ""),
          });
          break;
        case "generation_interrupted":
          handlers.onInterrupted?.({
            session_id: String(data.session_id || ""),
            message_id: String(data.message_id || ""),
            status: String(data.status || "interrupted"),
          });
          break;
        case "generation_completed":
          handlers.onCompleted?.({
            session_id: String(data.session_id || ""),
            message_id: String(data.message_id || ""),
          });
          break;
        case "error":
          handlers.onError?.(String(data.detail || "Error de chat"));
          break;
        default:
          break;
      }
    };

    socket.onerror = () => {
      /* onclose handles reconnect */
    };

    socket.onclose = () => {
      socket = null;
      if (!stopped) scheduleReconnect();
      else handlers.onConnectionChange?.("closed");
    };
  }

  open();

  return {
    stop() {
      stopped = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
      socket = null;
      handlers.onConnectionChange?.("closed");
    },
    sendUserMessage(text: string) {
      if (!sessionId) return;
      send({
        event: "user_message",
        data: { session_id: sessionId, text },
      });
    },
    interrupt(newInput?: string) {
      if (!sessionId) return;
      send({
        event: "interrupt_requested",
        data: {
          session_id: sessionId,
          ...(newInput ? { new_input: newInput } : {}),
        },
      });
    },
    getSessionId: () => sessionId,
  };
}
