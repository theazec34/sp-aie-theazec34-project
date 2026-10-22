/**
 * Proxy same-origin → API interna.
 * Más fiable que `rewrites` de next.config con Turbopack + Docker/Codespaces:
 * lee INTERNAL_API_URL en cada request (http://backend:8000 en Compose).
 */
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
  "host",
  "content-length",
]);

function upstreamBase(): string {
  return (
    process.env.INTERNAL_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000"
  ).replace(/\/$/, "");
}

async function proxy(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> }
): Promise<NextResponse> {
  const { path } = await context.params;
  const dest = `${upstreamBase()}/${path.join("/")}${req.nextUrl.search}`;

  const headers = new Headers();
  req.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });

  const init: RequestInit & { duplex?: "half" } = {
    method: req.method,
    headers,
    redirect: "manual",
    signal: AbortSignal.timeout(20_000),
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.arrayBuffer();
  }

  let upstream: Response;
  try {
    upstream = await fetch(dest, init);
  } catch (err) {
    const detail =
      err instanceof Error ? err.message : "upstream unreachable";
    return NextResponse.json(
      {
        detail:
          `Proxy /api-backend no alcanzó ${upstreamBase()} (${detail}). ` +
          `En Codespaces usa la URL …-8000.app.github.dev (puerto 8000 Public) ` +
          `o revisa: docker compose logs backend`,
      },
      { status: 502 }
    );
  }

  const outHeaders = new Headers();
  upstream.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      outHeaders.set(key, value);
    }
  });

  return new NextResponse(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: outHeaders,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
