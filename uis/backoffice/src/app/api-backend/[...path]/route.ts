/**
 * Proxy same-origin → API interna.
 *
 * Codespaces: TCP a backend:8000 suele TIMEOUT; host.docker.internal funciona.
 * BrasAI/RAG puede tardar >10s — primero elegimos upstream con /health (rápido),
 * luego reenviamos la petición real con timeout largo.
 */
import http from "node:http";
import https from "node:https";
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

const PROBE_MS = 2_500;
const DEFAULT_FORWARD_MS = 30_000;
const LONG_FORWARD_MS = 120_000;

function upstreamCandidates(): string[] {
  const primary = (
    process.env.INTERNAL_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://host.docker.internal:8000"
  ).replace(/\/$/, "");
  return [
    ...new Set([
      "http://host.docker.internal:8000",
      primary,
      "http://backend:8000",
      "http://brasaland-backend:8000",
    ]),
  ];
}

function forwardTimeoutMs(suffix: string): number {
  // RAG / setup / agent pueden superar 30s
  if (
    suffix.startsWith("/knowledge") ||
    suffix.startsWith("/rag") ||
    suffix.startsWith("/agent") ||
    suffix.startsWith("/rfp")
  ) {
    return LONG_FORWARD_MS;
  }
  return DEFAULT_FORWARD_MS;
}

function nodeFetch(
  dest: string,
  init: {
    method: string;
    headers?: Headers;
    body?: Buffer;
    timeoutMs: number;
  }
): Promise<{ status: number; statusText: string; headers: Headers; body: Buffer }> {
  const url = new URL(dest);
  const lib = url.protocol === "https:" ? https : http;
  const headers: Record<string, string> = {};
  init.headers?.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) headers[key] = value;
  });

  return new Promise((resolve, reject) => {
    const req = lib.request(
      {
        protocol: url.protocol,
        hostname: url.hostname,
        port: url.port || (url.protocol === "https:" ? 443 : 80),
        path: `${url.pathname}${url.search}`,
        method: init.method,
        headers,
        family: 4,
        timeout: init.timeoutMs,
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (c) => chunks.push(Buffer.isBuffer(c) ? c : Buffer.from(c)));
        res.on("end", () => {
          const out = new Headers();
          for (const [k, v] of Object.entries(res.headers)) {
            if (v == null || HOP_BY_HOP.has(k.toLowerCase())) continue;
            if (Array.isArray(v)) out.set(k, v.join(", "));
            else out.set(k, v);
          }
          resolve({
            status: res.statusCode || 502,
            statusText: res.statusMessage || "",
            headers: out,
            body: Buffer.concat(chunks),
          });
        });
      }
    );
    req.on("timeout", () => {
      req.destroy(new Error("timeout"));
    });
    req.on("error", reject);
    if (init.body) req.write(init.body);
    req.end();
  });
}

async function pickUpstream(): Promise<{ base: string } | { errors: string[] }> {
  const errors: string[] = [];
  for (const base of upstreamCandidates()) {
    try {
      const res = await nodeFetch(`${base}/health`, {
        method: "GET",
        timeoutMs: PROBE_MS,
      });
      if (res.status >= 200 && res.status < 500) {
        return { base };
      }
      errors.push(`${base}: HTTP ${res.status}`);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "unreachable";
      errors.push(`${base}: ${detail}`);
    }
  }
  return { errors };
}

async function proxy(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> }
): Promise<NextResponse> {
  const { path } = await context.params;
  const suffix = `/${path.join("/")}${req.nextUrl.search}`;

  const headers = new Headers();
  req.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) headers.set(key, value);
  });

  let body: Buffer | undefined;
  if (req.method !== "GET" && req.method !== "HEAD") {
    body = Buffer.from(await req.arrayBuffer());
  }

  const picked = await pickUpstream();
  if ("errors" in picked) {
    return NextResponse.json(
      {
        detail:
          `Proxy /api-backend no alcanzó la API (${picked.errors.join(" | ")}). ` +
          `Comprueba: curl -sS http://127.0.0.1:8000/health && docker compose ps. ` +
          `Si health OK: docker compose up -d --force-recreate --no-deps interfaces`,
      },
      { status: 502 }
    );
  }

  try {
    const upstream = await nodeFetch(`${picked.base}${suffix}`, {
      method: req.method,
      headers,
      body,
      timeoutMs: forwardTimeoutMs(suffix),
    });
    return new NextResponse(new Uint8Array(upstream.body), {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: upstream.headers,
    });
  } catch (err) {
    const detail = err instanceof Error ? err.message : "unreachable";
    return NextResponse.json(
      {
        detail: `Proxy /api-backend falló en ${picked.base}${suffix} (${detail}).`,
      },
      { status: 502 }
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
