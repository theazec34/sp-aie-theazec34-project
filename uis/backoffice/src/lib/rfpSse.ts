/**
 * Cliente SSE RFP vía fetch + ReadableStream (Bearer JWT).
 * Reconexión con backoff progresivo + Last-Event-ID + refetch al recuperar.
 */

import { getApiBaseUrl, getToken } from "./auth";

export type RfpTicketCreatedPayload = {
  ticket_id: number;
  status: string;
  original_filename?: string;
  client_name?: string | null;
  location?: string | null;
  service_type?: string | null;
  scope?: string | null;
  deadline?: string | null;
  budget_range?: string | null;
  departments_needed?: string[];
  created_at?: string;
  currency?: string;
  currency_symbol?: string;
};

export type SalesDropAlertPayload = {
  country: string;
  drop_pct: number;
  threshold_pct: number;
  week_label: string;
  notify?: string[];
  created_at?: string;
};

export type RfpSseHandlers = {
  onRfpTicketCreated?: (payload: RfpTicketCreatedPayload, eventId: string) => void;
  onSalesDropAlert?: (payload: SalesDropAlertPayload, eventId: string) => void;
  onConnectionChange?: (state: "connecting" | "open" | "reconnecting" | "closed") => void;
  /** Tras reconectar: refetch lista para no perder tickets (dedupe en UI). */
  onRecover?: () => void | Promise<void>;
};

const SEEN_KEY = "brasaland_rfp_sse_seen_ids";
const LAST_ID_KEY = "brasaland_rfp_sse_last_event_id";

function loadSeen(): Set<number> {
  try {
    const raw = sessionStorage.getItem(SEEN_KEY);
    if (!raw) return new Set();
    return new Set((JSON.parse(raw) as number[]).slice(-200));
  } catch {
    return new Set();
  }
}

function saveSeen(seen: Set<number>) {
  try {
    sessionStorage.setItem(SEEN_KEY, JSON.stringify([...seen].slice(-200)));
  } catch {
    /* ignore */
  }
}

export function markTicketSeen(ticketId: number): boolean {
  const seen = loadSeen();
  if (seen.has(ticketId)) return false;
  seen.add(ticketId);
  saveSeen(seen);
  return true;
}

export function getLastEventId(): string | null {
  try {
    return sessionStorage.getItem(LAST_ID_KEY);
  } catch {
    return null;
  }
}

function setLastEventId(id: string) {
  try {
    sessionStorage.setItem(LAST_ID_KEY, id);
  } catch {
    /* ignore */
  }
}

function parseSseChunk(buffer: string): { events: Array<{ id?: string; event?: string; data?: string }>; rest: string } {
  const parts = buffer.split("\n\n");
  const rest = parts.pop() ?? "";
  const events = [];
  for (const block of parts) {
    if (!block.trim() || block.trimStart().startsWith(":")) continue;
    let id: string | undefined;
    let event: string | undefined;
    const dataLines: string[] = [];
    for (const line of block.split("\n")) {
      if (line.startsWith("id:")) id = line.slice(3).trim();
      else if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
    }
    events.push({ id, event, data: dataLines.join("\n") });
  }
  return { events, rest };
}

export type RfpSseController = {
  stop: () => void;
};

/**
 * Abre el stream SSE. No usa EventSource (no soporta Authorization).
 */
export function connectRfpSse(handlers: RfpSseHandlers): RfpSseController {
  let stopped = false;
  let attempt = 0;
  let abort: AbortController | null = null;

  const backoffMs = () => Math.min(30_000, 1000 * 2 ** Math.min(attempt, 5));

  async function loop() {
    while (!stopped) {
      handlers.onConnectionChange?.(attempt === 0 ? "connecting" : "reconnecting");
      abort = new AbortController();
      const token = getToken();
      if (!token) {
        await sleep(backoffMs());
        attempt += 1;
        continue;
      }
      const apiBase = getApiBaseUrl().replace(/\/$/, "");
      const headers: Record<string, string> = {
        Accept: "text/event-stream",
        Authorization: `Bearer ${token}`,
      };
      const lastId = getLastEventId();
      if (lastId) headers["Last-Event-ID"] = lastId;

      try {
        const res = await fetch(`${apiBase}/rfp/events/stream`, {
          method: "GET",
          headers,
          signal: abort.signal,
        });
        if (!res.ok || !res.body) {
          throw new Error(`SSE HTTP ${res.status}`);
        }
        handlers.onConnectionChange?.("open");
        attempt = 0;
        // Recuperación: refetch lista (dedupe por ticket_id en UI)
        await handlers.onRecover?.();

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";
        while (!stopped) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const parsed = parseSseChunk(buf);
          buf = parsed.rest;
          for (const ev of parsed.events) {
            if (ev.id) setLastEventId(ev.id);
            if (!ev.event || !ev.data) continue;
            try {
              const data = JSON.parse(ev.data);
              if (ev.event === "rfp_ticket_created") {
                handlers.onRfpTicketCreated?.(data, ev.id || "");
              } else if (ev.event === "sales_drop_alert") {
                handlers.onSalesDropAlert?.(data, ev.id || "");
              }
            } catch {
              /* ignore malformed */
            }
          }
        }
      } catch (err) {
        if (stopped || (err instanceof DOMException && err.name === "AbortError")) {
          break;
        }
      }
      if (stopped) break;
      handlers.onConnectionChange?.("reconnecting");
      await sleep(backoffMs());
      attempt += 1;
    }
    handlers.onConnectionChange?.("closed");
  }

  void loop();

  return {
    stop() {
      stopped = true;
      abort?.abort();
    },
  };
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
