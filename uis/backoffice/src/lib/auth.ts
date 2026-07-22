const TOKEN_KEY = "brasaland_access_token";

export function getApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }
  const { protocol, hostname, port } = window.location;
  if (hostname.includes("github.dev") || hostname.includes("githubpreview.dev")) {
    const apiHost = hostname.replace(/-\d+(?=\.)/, "-8000");
    return `${protocol}//${apiHost}`;
  }
  if (port === "8000") {
    return window.location.origin;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
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
