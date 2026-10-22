import type { NextConfig } from "next";
import path from "path";

/**
 * Proxy API: `src/app/api-backend/[...path]/route.ts` (INTERNAL_API_URL en runtime).
 * Sin rewrites — en Codespaces/Turbopack el rewrite a backend:8000 hacía timeout
 * en formularios (reservas / candidaturas quedaban en «Enviando…»).
 */
const nextConfig: NextConfig = {
  turbopack: {
    root: path.join(__dirname),
  },
  images: {
    formats: ["image/avif", "image/webp"],
    deviceSizes: [640, 750, 828, 1080, 1200],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    // Evita errores "Single item size exceeds maxSize" con poco disco en Codespaces
    minimumCacheTTL: 60,
  },
};

export default nextConfig;
