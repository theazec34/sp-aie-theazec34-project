/**
 * Integraciones públicas website ↔ API.
 * Reservas/empleo: POST reales a FastAPI (TinyDB). La mesa/candidatura
 * queda en estado "recibida", no confirmada/contratada automáticamente.
 */

export const INTEGRATIONS = {
  reservations: {
    ready: true,
    mailtoFallback: true,
    path: "/reservations",
  },
  careers: {
    ready: true,
    mailtoFallback: true,
    path: "/careers",
  },
} as const;
