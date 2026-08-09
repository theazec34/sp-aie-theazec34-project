const TOKEN_KEY = "brasaland_access_token";
const API_BASE_KEY = "brasaland_api_base_url";

/** Default API URL from location / env (ignores localStorage override). */
function envApiBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_INVENTORY_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000"
  );
}

export function detectApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return envApiBaseUrl();
  }
  const { protocol, hostname, port } = window.location;
  if (hostname.includes("github.dev") || hostname.includes("githubpreview.dev")) {
    const apiHost = hostname.replace(/-\d+(?=\.)/, "-8000");
    return `${protocol}//${apiHost}`;
  }
  if (port === "8000") {
    return window.location.origin;
  }
  return envApiBaseUrl();
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

export function getApiBaseUrl(): string {
  return getStoredApiBaseUrl() || detectApiBaseUrl();
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
      `No se pudo conectar con la API (${apiBase}). Comprueba: ` +
      `1) uvicorn en el puerto 8000, ` +
      `2) en Codespaces el puerto 8000 en Public (no Private), ` +
      `3) la URL de API abajo (debe ser …-8000.app.github.dev, no localhost).`
    );
  }
  return raw;
}

/** OAuth2PasswordRequestForm login — username field carries the email. */
export async function loginRequest(
  apiBase: string,
  email: string,
  password: string
): Promise<string> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  const response = await fetch(`${apiBase.replace(/\/$/, "")}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

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
