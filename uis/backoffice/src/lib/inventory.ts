/**
 * Centralized inventory API client (CONTEXT Brasaland).
 * Components must call these helpers — no direct fetch in pages.
 *
 * Vocabulary (CONTEXT): Ingredient, IngredientEntry (entrada),
 * IngredientExit (salida), current_stock (calculado).
 */

import { apiFetch } from "./api";
import { readApiError } from "./errors";

export type IngredientCategory =
  | "meat"
  | "produce"
  | "sauce"
  | "beverage"
  | "packaging"
  | "cleaning";

export type IngredientCountry = "CO" | "US";
export type IngredientUnit = "kg" | "litro" | "unidad";
export type ExitReason = "consumption" | "waste";
export type OrderKind = "inbound" | "outbound";

export type Ingredient = {
  id: number;
  name: string;
  sku: string;
  unit: string;
  category: string;
  country: string;
  current_stock: number;
};

export type IngredientBrief = {
  id: number;
  name: string;
  sku: string;
  unit: string;
  category: string;
  country: string;
};

export type IngredientEntryCreate = {
  ingredient_id: number;
  quantity: number;
  supplier_name: string;
  location_id: number;
};

export type IngredientExitCreate = {
  ingredient_id: number;
  quantity: number;
  reason: ExitReason;
  location_id: number;
};

export type InventoryOrder = {
  kind: OrderKind;
  id: number;
  ingredient_id: number;
  quantity: number;
  location_id: number;
  created_at: string;
  user_uuid: string;
  supplier_name: string | null;
  reason: string | null;
  ingredient: IngredientBrief;
};

export const CATEGORY_LABELS: Record<string, string> = {
  meat: "Carne",
  produce: "Verdura",
  sauce: "Salsa",
  beverage: "Bebida",
  packaging: "Envase",
  cleaning: "Limpieza",
};

export const COUNTRY_LABELS: Record<string, string> = {
  CO: "Colombia",
  US: "EE.UU.",
};

export const REASON_LABELS: Record<ExitReason, string> = {
  consumption: "Consumo",
  waste: "Merma",
};

/**
 * Stock level thresholds for the products table (visual only).
 * - low: current_stock < LOW_STOCK_THRESHOLD (rojo)
 * - medium: LOW_STOCK_THRESHOLD <= stock < HEALTHY_STOCK_THRESHOLD (ámbar)
 * - healthy: stock >= HEALTHY_STOCK_THRESHOLD (verde)
 */
export const LOW_STOCK_THRESHOLD = 10;
export const HEALTHY_STOCK_THRESHOLD = 30;

export type StockLevel = "low" | "medium" | "healthy" | "empty";

export function stockLevel(currentStock: number): StockLevel {
  if (currentStock <= 0) return "empty";
  if (currentStock < LOW_STOCK_THRESHOLD) return "low";
  if (currentStock < HEALTHY_STOCK_THRESHOLD) return "medium";
  return "healthy";
}

export function stockLevelLabel(level: StockLevel): string {
  switch (level) {
    case "empty":
      return "Sin stock";
    case "low":
      return "Bajo";
    case "medium":
      return "Medio";
    case "healthy":
      return "Sano";
  }
}

async function ensureOk(response: Response): Promise<void> {
  if (response.ok) return;
  const parsed = await readApiError(response);
  throw new Error(parsed.message);
}

/** GET /inventory/products — JWT via apiFetch */
export async function listIngredients(): Promise<Ingredient[]> {
  const response = await apiFetch("/inventory/products");
  await ensureOk(response);
  return (await response.json()) as Ingredient[];
}

/** GET /inventory/products/{id} */
export async function getIngredient(id: number): Promise<Ingredient> {
  const response = await apiFetch(`/inventory/products/${id}`);
  await ensureOk(response);
  return (await response.json()) as Ingredient;
}

/** POST /inventory/orders/inbound */
export async function createInboundOrder(
  payload: IngredientEntryCreate
): Promise<{ id: number; ingredient_id: number; quantity: number }> {
  const response = await apiFetch("/inventory/orders/inbound", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await ensureOk(response);
  return (await response.json()) as {
    id: number;
    ingredient_id: number;
    quantity: number;
  };
}

/** POST /inventory/orders/outbound */
export async function createOutboundOrder(
  payload: IngredientExitCreate
): Promise<{ id: number; ingredient_id: number; quantity: number; reason: string }> {
  const response = await apiFetch("/inventory/orders/outbound", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await ensureOk(response);
  return (await response.json()) as {
    id: number;
    ingredient_id: number;
    quantity: number;
    reason: string;
  };
}

/** GET /inventory/orders */
export async function listOrders(): Promise<InventoryOrder[]> {
  const response = await apiFetch("/inventory/orders");
  await ensureOk(response);
  return (await response.json()) as InventoryOrder[];
}
