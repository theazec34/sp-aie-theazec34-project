import type { NextConfig } from "next";
import path from "path";

/**
 * El proxy a la API vive en `src/app/api-backend/[...path]/route.ts`
 * (lee INTERNAL_API_URL en runtime). No usamos rewrites aquí: con Turbopack
 * + Docker a veces el rewrite no resolvía backend:8000 y el login hacía timeout.
 */
const nextConfig: NextConfig = {
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
