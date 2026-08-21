/**
 * Brasaland Digital — TelemetryService (backoffice).
 *
 * Single entrypoint: track(eventType, properties).
 * Auto-fills envelope fields; queues batches; sendBeacon on hide;
 * retries with exponential backoff (max 3) then drops the batch.
 *
 * Profile/user PII must NEVER appear in properties.
 */

export const TELEMETRY_SCHEMA_VERSION = "1.0.0";
export const TELEMETRY_FLUSH_INTERVAL_MS = 10_000;
export const TELEMETRY_MAX_BATCH = 20;
export const TELEMETRY_MAX_RETRIES = 3;

const SESSION_KEY = "brasaland_telemetry_session_id";
const USER_KEY = "brasaland_telemetry_user_id";

export type TelemetryProperties = Record<string, unknown>;

export type TelemetryEvent = {
  eventId: string;
  timestamp: string;
  sessionId: string | null;
  userId: string | null;
  event_type: string;
  schemaVersion: string;
  requestId: string;
  properties: TelemetryProperties;
};

function uuid(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function readEndpoint(): string {
  const raw =
    process.env.NEXT_PUBLIC_TELEMETRY_ENDPOINT ||
    "http://localhost:8000/telemetry/events";
  return raw.replace(/\/$/, "");
}

/** Decode JWT `sub` without verifying (client convenience only). */
export function userIdFromToken(token: string | null): string | null {
  if (!token) return null;
  try {
    const part = token.split(".")[1];
    if (!part) return null;
    const json = JSON.parse(atob(part.replace(/-/g, "+").replace(/_/g, "/")));
    return json.sub != null ? String(json.sub) : null;
  } catch {
    return null;
  }
}

class TelemetryServiceImpl {
  private queue: TelemetryEvent[] = [];
  private timer: ReturnType<typeof setInterval> | null = null;
  private flushing = false;
  private started = false;
  private sessionId: string | null = null;
  private userId: string | null = null;

  /** Call once from client layout / bootstrap. */
  start(): void {
    if (typeof window === "undefined" || this.started) return;
    this.started = true;
    this.ensureSession();
    this.restoreUser();
    this.timer = setInterval(() => {
      void this.flush("interval");
    }, TELEMETRY_FLUSH_INTERVAL_MS);

    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") {
        this.flushBeacon();
      }
    });
    window.addEventListener("pagehide", () => this.flushBeacon());

    window.addEventListener("error", (event) => {
      this.track("frontend_error_captured", {
        route: window.location.pathname,
        error_name: event.error?.name || "Error",
        message_sanitized: String(event.message || "error").slice(0, 200),
      });
    });
    window.addEventListener("unhandledrejection", (event) => {
      const reason = event.reason;
      const message =
        reason instanceof Error
          ? reason.message
          : typeof reason === "string"
            ? reason
            : "unhandledrejection";
      this.track("frontend_error_captured", {
        route: window.location.pathname,
        error_name: reason instanceof Error ? reason.name : "UnhandledRejection",
        message_sanitized: message.slice(0, 200),
      });
    });
  }

  ensureSession(): string {
    if (typeof window === "undefined") return "";
    let id = sessionStorage.getItem(SESSION_KEY);
    if (!id) {
      id = uuid();
      sessionStorage.setItem(SESSION_KEY, id);
    }
    this.sessionId = id;
    return id;
  }

  /** Persist opaque user id after login (TinyDB id as string). */
  setUserId(userId: string | null): void {
    this.userId = userId;
    if (typeof window === "undefined") return;
    if (userId) sessionStorage.setItem(USER_KEY, userId);
    else sessionStorage.removeItem(USER_KEY);
  }

  clearUser(): void {
    this.setUserId(null);
  }

  private restoreUser(): void {
    if (typeof window === "undefined") return;
    this.userId = sessionStorage.getItem(USER_KEY);
  }

  /**
   * Sole public tracking API. Callers pass only event_type + allowlisted properties.
   */
  track(eventType: string, properties: TelemetryProperties = {}): void {
    if (typeof window === "undefined") return;
    this.ensureSession();
    const event: TelemetryEvent = {
      eventId: uuid(),
      timestamp: new Date().toISOString(),
      sessionId: this.sessionId,
      userId: this.userId,
      event_type: eventType,
      schemaVersion: TELEMETRY_SCHEMA_VERSION,
      requestId: uuid(),
      properties: { ...properties },
    };
    this.queue.push(event);
    if (this.queue.length >= TELEMETRY_MAX_BATCH) {
      void this.flush("max_batch");
    }
  }

  private takeBatch(): TelemetryEvent[] {
    if (this.queue.length === 0) return [];
    const batch = this.queue.slice();
    this.queue = [];
    return batch;
  }

  private requeue(events: TelemetryEvent[]): void {
    this.queue = events.concat(this.queue);
  }

  async flush(_reason: string = "manual"): Promise<void> {
    if (this.flushing || typeof window === "undefined") return;
    const batch = this.takeBatch();
    if (batch.length === 0) return;
    this.flushing = true;
    try {
      await this.sendWithRetry(batch, 0);
    } finally {
      this.flushing = false;
    }
  }

  private flushBeacon(): void {
    if (typeof window === "undefined" || typeof navigator.sendBeacon !== "function") {
      void this.flush("beacon_fallback");
      return;
    }
    const batch = this.takeBatch();
    if (batch.length === 0) return;
    const body = JSON.stringify({ events: batch });
    const blob = new Blob([body], { type: "application/json" });
    const ok = navigator.sendBeacon(readEndpoint(), blob);
    if (!ok) {
      this.requeue(batch);
    }
  }

  private async sendWithRetry(
    batch: TelemetryEvent[],
    attempt: number
  ): Promise<void> {
    const endpoint = readEndpoint();
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ events: batch }),
        keepalive: true,
      });
      if (!response.ok) {
        throw new Error(`telemetry HTTP ${response.status}`);
      }
    } catch {
      if (attempt >= TELEMETRY_MAX_RETRIES) {
        // Non-critical: drop batch after N failures.
        return;
      }
      const delay = 250 * 2 ** attempt;
      await new Promise((r) => setTimeout(r, delay));
      await this.sendWithRetry(batch, attempt + 1);
    }
  }

  /** Test helper */
  _queueSize(): number {
    return this.queue.length;
  }
}

export const telemetry = new TelemetryServiceImpl();

/** Public API required by the milestone. */
export function track(
  eventType: string,
  properties: TelemetryProperties = {}
): void {
  telemetry.track(eventType, properties);
}
