/**
 * Browser → API via same-origin proxy `/api-backend/*`
 * (Route Handler → INTERNAL_API_URL / backend).
 * Para forzar URL directa: NEXT_PUBLIC_API_DIRECT=1 + NEXT_PUBLIC_API_URL.
 */
export function getPublicApiBase(): string {
  if (process.env.NEXT_PUBLIC_API_DIRECT === "1") {
    return (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(
      /\/$/,
      ""
    );
  }
  return "/api-backend";
}

const POST_TIMEOUT_MS = 15_000;

export async function postJson<T>(
  path: string,
  body: unknown
): Promise<{ ok: true; data: T } | { ok: false; status: number; detail: string }> {
  const base = getPublicApiBase().replace(/\/$/, "");
  const url = path.startsWith("http")
    ? path
    : `${base}${path.startsWith("/") ? "" : "/"}${path}`;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(POST_TIMEOUT_MS),
    });
    const payload = (await res.json().catch(() => ({}))) as {
      detail?: string | Array<{ msg?: string }>;
      message?: string;
      status_message?: string;
    };
    if (!res.ok) {
      let detail = `Error ${res.status}`;
      if (typeof payload.detail === "string") detail = payload.detail;
      else if (Array.isArray(payload.detail) && payload.detail[0]?.msg) {
        detail = payload.detail[0].msg;
      }
      return { ok: false, status: res.status, detail };
    }
    return { ok: true, data: payload as T };
  } catch (err) {
    const name = err instanceof Error ? err.name : "";
    if (name === "TimeoutError" || name === "AbortError") {
      return {
        ok: false,
        status: 0,
        detail:
          "La API no respondió a tiempo. Comprueba que el backend esté sano " +
          "(curl :8000/health) y reintenta. En Codespaces el puerto 8000 debe ser Public.",
      };
    }
    return {
      ok: false,
      status: 0,
      detail:
        "No se pudo contactar con la API. Comprueba que el backend esté en marcha.",
    };
  }
}
