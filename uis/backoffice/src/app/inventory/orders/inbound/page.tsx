"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import AppNav from "../../../../components/AppNav";
import RequireAuth from "../../../../components/RequireAuth";
import { getApiBaseUrl } from "../../../../lib/auth";
import { friendlyCatch } from "../../../../lib/errors";
import {
  createInboundOrder,
  getIngredient,
  Ingredient,
  listIngredients,
  LOW_STOCK_THRESHOLD,
} from "../../../../lib/inventory";
import { track } from "../../../../services/telemetry";
import {
  baselineKey,
  inventoryBaseProps,
  isBelowThreshold,
  readBaselines,
  writeBaseline,
} from "../../../../lib/telemetryInventory";

function InboundForm() {
  const searchParams = useSearchParams();
  const presetId = searchParams.get("ingredient_id");

  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [ingredientId, setIngredientId] = useState(presetId || "");
  const [quantity, setQuantity] = useState("");
  const [supplierName, setSupplierName] = useState("");
  const [locationId, setLocationId] = useState("1");
  const [unitCost, setUnitCost] = useState("");
  const [loading, setLoading] = useState(false);
  const [bootLoading, setBootLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setBootLoading(true);
      try {
        const data = await listIngredients();
        if (!cancelled) {
          setIngredients(data);
          if (presetId) setIngredientId(presetId);
        }
      } catch (err) {
        if (!cancelled) setError(friendlyCatch(err, getApiBaseUrl()));
      } finally {
        if (!cancelled) setBootLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [presetId]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);
    const item = ingredients.find((i) => i.id === Number(ingredientId));
    const loc = Number(locationId);
    const qty = Number(quantity);
    try {
      if (!item) throw new Error("Ingrediente no encontrado");
      const created = await createInboundOrder({
        ingredient_id: Number(ingredientId),
        quantity: qty,
        supplier_name: supplierName.trim(),
        location_id: loc,
      });
      const base = inventoryBaseProps(item, loc, qty);
      track("inbound_order_created", {
        ...base,
        supplier_name: supplierName.trim(),
        order_id: created.id,
        ...(unitCost ? { unit_cost: Number(unitCost) } : {}),
      });

      if (unitCost) {
        const cost = Number(unitCost);
        const key = baselineKey(item.id, supplierName);
        const baselines = readBaselines();
        const baseline = baselines[key];
        if (baseline && baseline > 0) {
          const variance = (cost - baseline) / baseline;
          if (Math.abs(variance) >= 0.1) {
            track("ingredient_price_variance_detected", {
              location_id: loc,
              country: base.country,
              product_id: item.id,
              product_category: item.category,
              unit: item.unit,
              currency: base.currency,
              supplier_name: supplierName.trim(),
              unit_cost: cost,
              baseline_unit_cost: baseline,
              variance_pct: Math.round(variance * 1000) / 1000,
              threshold_pct: 0.1,
              order_id: created.id,
            });
          }
        }
        writeBaseline(key, cost);
      }

      const refreshed = await getIngredient(item.id);
      if (isBelowThreshold(refreshed.current_stock)) {
        track("stock_threshold_triggered", {
          location_id: loc,
          country: base.country,
          product_id: item.id,
          product_category: item.category,
          unit: item.unit,
          current_stock: refreshed.current_stock,
          threshold: LOW_STOCK_THRESHOLD,
          triggering_order_kind: "inbound",
          triggering_order_id: created.id,
        });
      }

      setQuantity("");
      setSupplierName("");
      setUnitCost("");
      setLocationId("1");
      setMessage("Entrada de ingrediente registrada correctamente.");
    } catch (err) {
      track("inventory_validation_failed", {
        route: "/inventory/orders/inbound",
        field: "form",
        message_key: "inbound_failed",
        http_status: 400,
      });
      setError(friendlyCatch(err, getApiBaseUrl()));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <header className="bo-topbar">
        <div>
          <p className="bo-kicker">Inventario · IngredientEntry</p>
          <h1>Registrar entrada (proveedor)</h1>
        </div>
        <Link className="bo-btn" href="/inventory/products">
          Volver al stock
        </Link>
      </header>

      <section className="bo-panel" style={{ maxWidth: 640 }}>
        {bootLoading ? <p className="bo-soft">Cargando ingredientes…</p> : null}
        {error ? <p className="bo-alert bo-alert-error">{error}</p> : null}
        {message ? <p className="bo-alert bo-alert-ok">{message}</p> : null}

        <form className="auth-form" onSubmit={onSubmit}>
          <label className="bo-field">
            <span>Ingrediente</span>
            <select
              required
              value={ingredientId}
              onChange={(e) => setIngredientId(e.target.value)}
              disabled={loading || bootLoading}
            >
              <option value="">Selecciona un ingrediente</option>
              {ingredients.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} ({item.sku}) — stock {item.current_stock} {item.unit}
                </option>
              ))}
            </select>
          </label>

          <label className="bo-field">
            <span>Cantidad</span>
            <input
              required
              type="number"
              min={0.01}
              step="any"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              disabled={loading}
            />
          </label>

          <label className="bo-field">
            <span>Proveedor (supplier_name)</span>
            <input
              required
              value={supplierName}
              onChange={(e) => setSupplierName(e.target.value)}
              disabled={loading}
              placeholder="Carnes del Valle S.A."
            />
          </label>

          <label className="bo-field">
            <span>Costo unitario (opcional · telemetría / moneda del local)</span>
            <input
              type="number"
              min={0.01}
              step="any"
              value={unitCost}
              onChange={(e) => setUnitCost(e.target.value)}
              disabled={loading}
              placeholder="Ej. 12500 (COP) o 4.5 (USD)"
            />
          </label>

          <label className="bo-field">
            <span>Local (location_id 1–14)</span>
            <input
              required
              type="number"
              min={1}
              max={14}
              value={locationId}
              onChange={(e) => setLocationId(e.target.value)}
              disabled={loading}
            />
          </label>

          <button type="submit" className="bo-btn" disabled={loading || bootLoading}>
            {loading ? "Guardando…" : "Registrar entrada"}
          </button>
        </form>
      </section>
    </>
  );
}

export default function InboundOrderPage() {
  return (
    <RequireAuth>
      <main className="bo-shell">
        <AppNav active="inventory-inbound" />
        <section className="bo-content">
          <Suspense fallback={<p className="bo-soft">Cargando formulario…</p>}>
            <InboundForm />
          </Suspense>
        </section>
      </main>
    </RequireAuth>
  );
}
