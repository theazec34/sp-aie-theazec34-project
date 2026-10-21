/**
 * Integraciones pendientes (no hay envío real desde el navegador aún).
 *
 * Reservas:
 *  - Endpoint sugerido: POST /api/reservations (FastAPI) o proveedor (CoverManager, TheFork…).
 *  - Payload: { fullName, phone, email, date, time, guests, notes }
 *  - Hasta entonces ReservationForm valida y ofrece mailto.
 *
 * Empleo:
 *  - Endpoint sugerido: POST /api/careers (+ almacenamiento CV) o ATS.
 *  - Hasta entonces JobApplicationForm valida y ofrece mailto a rrhh@.
 *
 * No marcar UI como "enviado / confirmado" sin 2xx del backend.
 */

export const INTEGRATIONS = {
  reservations: {
    ready: false,
    mailtoFallback: true,
    suggestedPath: "/api/reservations",
  },
  careers: {
    ready: false,
    mailtoFallback: true,
    suggestedPath: "/api/careers",
  },
} as const;
