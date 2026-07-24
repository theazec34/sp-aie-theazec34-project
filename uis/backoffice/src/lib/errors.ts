/** Human-readable API / network errors for the backoffice UI. */

import { networkErrorMessage } from "./auth";

export type FieldErrors = Record<string, string>;

export function parseApiErrorPayload(detail: unknown): {
  message: string;
  fieldErrors: FieldErrors;
} {
  const fieldErrors: FieldErrors = {};
  if (!detail || typeof detail !== "object") {
    return { message: "No se pudo completar la operación.", fieldErrors };
  }

  const body = detail as {
    detail?: unknown;
    errors?: Array<{ field?: string; message?: string }>;
  };

  if (Array.isArray(body.errors)) {
    for (const item of body.errors) {
      if (item?.field) {
        fieldErrors[item.field] = item.message || "Valor inválido";
      }
    }
    return {
      message:
        typeof body.detail === "string"
          ? body.detail
          : "Revisa los campos marcados.",
      fieldErrors,
    };
  }

  if (typeof body.detail === "string") {
    return { message: body.detail, fieldErrors };
  }

  if (
    body.detail &&
    typeof body.detail === "object" &&
    "message" in (body.detail as object)
  ) {
    const nested = body.detail as { field?: string; message?: string };
    if (nested.field) {
      fieldErrors[nested.field] = nested.message || "Valor inválido";
    }
    return {
      message: nested.message || "No se pudo completar la operación.",
      fieldErrors,
    };
  }

  if (Array.isArray(body.detail)) {
    for (const item of body.detail as Array<{ loc?: unknown[]; msg?: string }>) {
      const field = Array.isArray(item.loc)
        ? String(item.loc.at(-1) ?? "form")
        : "form";
      fieldErrors[field] = item.msg || "Valor inválido";
    }
    return { message: "Revisa los campos marcados.", fieldErrors };
  }

  return { message: "No se pudo completar la operación.", fieldErrors };
}

export async function readApiError(
  response: Response
): Promise<{ message: string; fieldErrors: FieldErrors }> {
  try {
    const payload = await response.json();
    return parseApiErrorPayload(payload);
  } catch {
    // ignore JSON parse errors
  }

  if (response.status >= 500) {
    return {
      message:
        "El servidor no responde correctamente. Reinténtalo o contacta con soporte.",
      fieldErrors: {},
    };
  }
  if (response.status === 404) {
    return { message: "No se encontró el recurso solicitado.", fieldErrors: {} };
  }
  return {
    message: "No se pudo completar la operación. Reinténtalo en unos segundos.",
    fieldErrors: {},
  };
}

export function friendlyCatch(err: unknown, apiBase: string): string {
  return networkErrorMessage(err, apiBase);
}
