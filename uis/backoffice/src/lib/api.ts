import { clearToken, getApiBaseUrl, getToken } from "./auth";
import { track } from "../services/telemetry";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

type FetchOptions = RequestInit & {
  /** If true, do not attach Authorization header. */
  skipAuth?: boolean;
};

/**
 * Authenticated fetch helper:
 * - attaches Bearer token from localStorage
 * - on 401 clears token and redirects to /login
 * - samples API latency for telemetry (non-blocking)
 */
export async function apiFetch(
  path: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { skipAuth, headers, ...rest } = options;
  const apiBase = getApiBaseUrl().replace(/\/$/, "");
  const url = path.startsWith("http") ? path : `${apiBase}${path}`;

  const finalHeaders = new Headers(headers || {});
  if (!skipAuth) {
    const token = getToken();
    if (token) {
      finalHeaders.set("Authorization", `Bearer ${token}`);
    }
  }

  const started = performance.now();
  const response = await fetch(url, { ...rest, headers: finalHeaders });
  const durationMs = performance.now() - started;

  // Sample ~10% of calls (always record if slow > 500ms)
  if (durationMs > 500 || Math.random() < 0.1) {
    const route = path.startsWith("http")
      ? new URL(path).pathname
      : path.split("?")[0];
    track("api_latency_recorded", {
      route,
      method: (rest.method || "GET").toUpperCase(),
      status_code: response.status,
      duration_ms: Math.round(durationMs * 10) / 10,
      cache_status: response.headers.get("X-Cache") || "NA",
    });
  }

  if (response.status === 401 && !skipAuth) {
    track("auth_session_expired", {
      route: typeof window !== "undefined" ? window.location.pathname : path,
      http_status: 401,
    });
    clearToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new ApiError("Sesión expirada o no autenticada", 401);
  }

  return response;
}

export function logoutAndRedirect(): void {
  clearToken();
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}
