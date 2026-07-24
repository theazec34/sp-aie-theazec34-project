/** Valores exactos del CONTEXT — gestor de incidencias centralizado. */

export const INCIDENT_STATUSES = [
  { value: "open", label: "Abierta" },
  { value: "in_progress", label: "En progreso" },
  { value: "resolved", label: "Resuelta" },
  { value: "discarded", label: "Descartada" },
] as const;

export const INCIDENT_ORIGINS = [
  { value: "customer", label: "Cliente" },
  { value: "branch", label: "Sede" },
  { value: "internal", label: "Interna" },
] as const;

export const INCIDENT_CATEGORIES = [
  { value: "equipment_failure", label: "Fallo de equipamiento" },
  { value: "supply_issue", label: "Problema de insumos" },
  { value: "customer_complaint", label: "Queja de cliente" },
  { value: "staff_issue", label: "Incidencia de personal" },
  { value: "facility_issue", label: "Instalaciones" },
  { value: "pos_system", label: "Sistema de caja / TPV" },
  { value: "delivery_issue", label: "Delivery" },
  { value: "other", label: "Otra" },
] as const;

export const INCIDENT_BRANCHES = [
  { value: "central", label: "Central (Medellín / Miami)" },
  { value: "medellin_centro", label: "Medellín Centro" },
  { value: "medellin_laureles", label: "Medellín Laureles" },
  { value: "medellin_envigado", label: "Medellín Envigado" },
  { value: "medellin_bello", label: "Medellín Bello" },
  { value: "medellin_itagui", label: "Medellín Itagüí" },
  { value: "bogota_chapinero", label: "Bogotá Chapinero" },
  { value: "bogota_usaquen", label: "Bogotá Usaquén" },
  { value: "cali_granada", label: "Cali Granada" },
  { value: "barranquilla_norte", label: "Barranquilla Norte" },
  { value: "miami_doral", label: "Miami Doral" },
  { value: "miami_hialeah", label: "Miami Hialeah" },
  { value: "miami_kendall", label: "Miami Kendall" },
  { value: "orlando_international", label: "Orlando International Drive" },
  { value: "fort_lauderdale", label: "Fort Lauderdale" },
] as const;

export type Incident = {
  id: number;
  title: string;
  description: string;
  category: string;
  status: string;
  origin: string;
  branch: string;
  created_at: string;
  updated_at: string;
};

export type IncidentSummary = {
  total: number;
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  by_origin: Record<string, number>;
  by_branch: Record<string, number>;
};

export const STATUS_TRANSITIONS: Record<string, string[]> = {
  open: ["in_progress", "discarded"],
  in_progress: ["resolved", "discarded"],
  resolved: [],
  discarded: [],
};

export function labelFor(
  options: readonly { value: string; label: string }[],
  value: string
): string {
  return options.find((item) => item.value === value)?.label || value;
}
