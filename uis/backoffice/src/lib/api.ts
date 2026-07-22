import { clearToken, getApiBaseUrl, getToken } from "./auth";

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

  const response = await fetch(url, { ...rest, headers: finalHeaders });

  if (response.status === 401 && !skipAuth) {
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
