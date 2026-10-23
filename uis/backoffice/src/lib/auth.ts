const TOKEN_KEY = "brasaland_access_token";
const API_BASE_KEY = "brasaland_api_base_url";

/**
 * Browser → API via same-origin proxy `/api-backend/*`
 * (Next rewrite → INTERNAL_API_URL / backend). Evita localhost:8000 roto
 * en Codespaces / Docker desde el navegador.
 * Forzar URL directa: NEXT_PUBLIC_API_DIRECT=1 + NEXT_PUBLIC_API_URL.
 */
function envApiBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_DIRECT === "1") {
    return (
      process.env.NEXT_PUBLIC_INVENTORY_API_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:8000"
    ).replace(/\/$/, "");
  }
  return "/api-backend";
}

/** Absolute API origin for WebSocket (Next rewrite no hace upgrade WS). */
export function getDirectApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    if (hostname.includes("github.dev") || hostname.includes("githubpreview.dev")) {
      const apiHost = hostname.replace(/-\d+(?=\.)/, "-8000");
      return `${protocol}//${apiHost}`;
    }
  }
  return (
    process.env.NEXT_PUBLIC_INVENTORY_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000"
  ).replace(/\/$/, "");
}

export function detectApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return envApiBaseUrl();
  }
  const { port } = window.location;
  // Codespaces / Docker: same-origin `/api-backend` (Route Handler → backend).
  // La URL pública …-8000.app.github.dev falla a menudo (puerto Private / DNS).
  // WebSocket del agente sigue usando getDirectApiBaseUrl() → puerto 8000.
  if (process.env.NEXT_PUBLIC_API_DIRECT === "1") {
    if (port === "8000") {
      return window.location.origin;
    }
    return (
      process.env.NEXT_PUBLIC_INVENTORY_API_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:8000"
    ).replace(/\/$/, "");
  }
  return "/api-backend";
}

export function getStoredApiBaseUrl(): string | null {
  if (typeof window === "undefined") return null;
  const value = localStorage.getItem(API_BASE_KEY)?.trim();
  return value || null;
}

export function setStoredApiBaseUrl(url: string): void {
  const cleaned = url.trim().replace(/\/$/, "");
  if (cleaned) {
    localStorage.setItem(API_BASE_KEY, cleaned);
  } else {
    localStorage.removeItem(API_BASE_KEY);
  }
}

/** Ignore stale overrides that break Codespaces (localhost o …-8000 públicos rotos). */
function shouldIgnoreStored(url: string): boolean {
  if (typeof window === "undefined") return false;
  const host = window.location.hostname;
  const onCodespace =
    host.includes("github.dev") || host.includes("githubpreview.dev");
  if (!onCodespace) return false;
  const cleaned = url.replace(/\/$/, "");
  // Preferir siempre el proxy; ignorar overrides a localhost o al puerto 8000 público
  if (/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?\/?$/i.test(cleaned)) {
    return true;
  }
  if (/^https?:\/\/[^/]*-8000\.(app\.)?github(preview)?\.dev\/?$/i.test(cleaned)) {
    return true;
  }
  return false;
}

export function getApiBaseUrl(): string {
  const stored = getStoredApiBaseUrl();
  if (stored && !shouldIgnoreStored(stored)) {
    return stored.replace(/\/$/, "");
  }
  return detectApiBaseUrl();
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return Boolean(getToken());
}

/** Human-readable message when fetch cannot reach the API at all. */
export function networkErrorMessage(err: unknown, apiBase: string): string {
  const raw = err instanceof Error ? err.message : String(err);
  if (/failed to fetch|networkerror|load failed|network request failed/i.test(raw)) {
    return (
      `No se pudo conectar con la API (${apiBase}). Comprueba que el backend ` +
      `esté en marcha y usa «Usar auto-detectada» en la URL de la API.`
    );
  }
  return raw;
}

const LOGIN_TIMEOUT_MS = 12_000;

/** OAuth2PasswordRequestForm login — username field carries the email. */
export async function loginRequest(
  apiBase: string,
  email: string,
  password: string
): Promise<string> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  const url = `${apiBase.replace(/\/$/, "")}/auth/login`;
  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
      signal: AbortSignal.timeout(LOGIN_TIMEOUT_MS),
    });
  } catch (err) {
    const name = err instanceof Error ? err.name : "";
    if (name === "TimeoutError" || name === "AbortError") {
      throw new Error(
        `La API no respondió a tiempo (${apiBase}). ` +
          `Espera a que brasaland-backend esté sano (curl :8000/health) y reintenta. ` +
          `Si usas Docker: docker compose logs backend`
      );
    }
    throw err;
  }

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(
      typeof detail.detail === "string"
        ? detail.detail
        : "No se pudo iniciar sesión. Revisa email y contraseña."
    );
  }

  const data = (await response.json()) as { access_token: string };
  return data.access_token;
}
