/**
 * Helpers to build allowlisted inventory telemetry properties.
 * Maps Ingredient (code) → Product (CONTEXT) field names.
 */

import {
  LOW_STOCK_THRESHOLD,
  type Ingredient,
  type ExitReason,
} from "../lib/inventory";

export type WasteReason = "expired" | "kitchen_error" | "theft_suspected";

const PRICE_BASELINE_KEY = "brasaland_unit_cost_baseline";

export function currencyForCountry(country: string): "COP" | "USD" {
  return country === "US" ? "USD" : "COP";
}

export function inventoryBaseProps(
  item: Ingredient,
  locationId: number,
  quantity: number
) {
  return {
    location_id: locationId,
    country: item.country === "US" ? "US" : "CO",
    product_id: item.id,
    product_sku: item.sku,
    product_category: item.category,
    quantity,
    unit: item.unit,
    currency: currencyForCountry(item.country),
  };
}

export function readBaselines(): Record<string, number> {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(sessionStorage.getItem(PRICE_BASELINE_KEY) || "{}") as Record<
      string,
      number
    >;
  } catch {
    return {};
  }
}

export function writeBaseline(key: string, unitCost: number): void {
  if (typeof window === "undefined") return;
  const map = readBaselines();
  map[key] = unitCost;
  sessionStorage.setItem(PRICE_BASELINE_KEY, JSON.stringify(map));
}

export function baselineKey(productId: number, supplierName: string): string {
  return `${productId}::${supplierName.trim().toLowerCase()}`;
}

/** Map API ExitReason + optional waste detail to CONTEXT taxonomy. */
export function resolveWasteReason(
  reason: ExitReason,
  wasteDetail?: WasteReason
): WasteReason | null {
  if (reason !== "waste") return null;
  return wasteDetail || "expired";
}

export function isBelowThreshold(stock: number, threshold = LOW_STOCK_THRESHOLD): boolean {
  return stock < threshold;
}
