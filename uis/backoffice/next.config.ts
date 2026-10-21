import type { NextConfig } from "next";
import path from "path";

/** Server-side target for /api-backend rewrite (Docker: http://backend:8000). */
const rewriteTarget = (
  process.env.INTERNAL_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

const nextConfig: NextConfig = {
  turbopack: {
    root: path.join(__dirname),
  },
  async rewrites() {
    return [
      {
        source: "/api-backend/:path*",
        destination: `${rewriteTarget}/:path*`,
      },
    ];
  },
};

export default nextConfig;
