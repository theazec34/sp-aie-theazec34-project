"use client";

import { FormEvent, Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import AppNav from "../../../../components/AppNav";
import RequireAuth from "../../../../components/RequireAuth";
import { getApiBaseUrl } from "../../../../lib/auth";
import { friendlyCatch } from "../../../../lib/errors";
import {
  createOutboundOrder,
  ExitReason,
  getIngredient,
  Ingredient,
  listIngredients,
  LOW_STOCK_THRESHOLD,
  REASON_LABELS,
} from "../../../../lib/inventory";
import { track } from "../../../../services/telemetry";
import {
  inventoryBaseProps,
  isBelowThreshold,
  resolveWasteReason,
  type WasteReason,
} from "../../../../lib/telemetryInventory";

function OutboundForm() {
  const searchParams = useSearchParams();
  const presetId = searchParams.get("ingredient_id");

  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [ingredientId, setIngredientId] = useState(presetId || "");
  const [selected, setSelected] = useState<Ingredient | null>(null);
  const [quantity, setQuantity] = useState("");
  const [reason, setReason] = useState<ExitReason>("consumption");
  const [wasteDetail, setWasteDetail] = useState<WasteReason>("expired");
  const [locationId, setLocationId] = useState("1");
  const [loading, setLoading] = useState(false);
  const [bootLoading, setBootLoading] = useState(true);
  const [error, setError] = useState("");
  const [quantityError, setQuantityError] = useState("");
  const [clientWarning, setClientWarning] = useState("");
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

  useEffect(() => {
    if (!ingredientId) {
      setSelected(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const item = await getIngredient(Number(ingredientId));
        if (!cancelled) setSelected(item);
      } catch (err) {
        if (!cancelled) {
          setSelected(null);
          setError(friendlyCatch(err, getApiBaseUrl()));
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [ingredientId]);

  const available = selected?.current_stock ?? null;

  const qtyNumber = useMemo(() => Number(quantity), [quantity]);

  useEffect(() => {
    if (!quantity || available === null || Number.isNaN(qtyNumber)) {
      setClientWarning("");
      return;
    }
    if (qtyNumber > available) {
      setClientWarning(
        `La cantidad (${qtyNumber}) supera el stock disponible (${available}). La API rechazará el envío.`
      );
    } else {
      setClientWarning("");
    }
  }, [qtyNumber, quantity, available]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setQuantityError("");
    setMessage("");
    setLoading(true);
    const loc = Number(locationId);
    const qty = Number(quantity);
    const item =
      selected || ingredients.find((i) => i.id === Number(ingredientId)) || null;
    try {
      if (!item) throw new Error("Ingrediente no encontrado");
      const created = await createOutboundOrder({
        ingredient_id: Number(ingredientId),
        quantity: qty,
        reason,
        location_id: loc,
      });
      const base = inventoryBaseProps(item, loc, qty);
      if (reason === "consumption") {
        track("outbound_order_created", {
          ...base,
          reason: "consumption",
          order_id: created.id,
        });
      } else {
        const wasteReason = resolveWasteReason(reason, wasteDetail) || "expired";
        track("stock_waste_registered", {
          ...base,
          reason: wasteReason,
          order_id: created.id,
        });
      }

      const refreshed = await getIngredient(Number(ingredientId));
      setSelected(refreshed);
      setIngredients((prev) =>
        prev.map((row) => (row.id === refreshed.id ? refreshed : row))
      );
      if (isBelowThreshold(refreshed.current_stock)) {
        track("stock_threshold_triggered", {
          location_id: loc,
          country: base.country,
          product_id: item.id,
          product_category: item.category,
          unit: item.unit,
          current_stock: refreshed.current_stock,
          threshold: LOW_STOCK_THRESHOLD,
          triggering_order_kind: "outbound",
          triggering_order_id: created.id,
        });
      }

      setQuantity("");
      setReason("consumption");
      setWasteDetail("expired");
      setLocationId("1");
      setMessage("Salida de ingrediente registrada correctamente.");
    } catch (err) {
      const text = friendlyCatch(err, getApiBaseUrl());
      setError(text);
      if (
        text.toLowerCase().includes("insufficient stock") ||
        text.toLowerCase().includes("stock")
      ) {
        setQuantityError(text);
        if (item) {
          track("outbound_order_rejected", {
            ...inventoryBaseProps(item, loc, qty),
            error_code: "insufficient_stock",
            available_stock: item.current_stock,
          });
        }
      } else {
        track("inventory_validation_failed", {
          route: "/inventory/orders/outbound",
          field: "form",
          message_key: "outbound_failed",
          http_status: 400,
        });
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <header className="bo-topbar">
        <div>
          <p className="bo-kicker">Inventario · IngredientExit</p>
          <h1>Registrar salida (consumo / merma)</h1>
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
              onChange={(e) => {
                setIngredientId(e.target.value);
                setQuantityError("");
                setError("");
              }}
              disabled={loading || bootLoading}
            >
              <option value="">Selecciona un ingrediente</option>
              {ingredients.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} ({item.sku})
                </option>
              ))}
            </select>
          </label>

          {selected ? (
            <p className="bo-alert bo-alert-ok" role="status">
              Stock actual de <strong>{selected.name}</strong>:{" "}
              <strong>
                {selected.current_stock} {selected.unit}
              </strong>{" "}
              (antes de enviar)
            </p>
          ) : (
            <p className="bo-soft">Selecciona un ingrediente para ver el stock disponible.</p>
          )}

          <label className="bo-field">
            <span>Cantidad</span>
            <input
              required
              type="number"
              min={0.01}
              step="any"
              value={quantity}
              onChange={(e) => {
                setQuantity(e.target.value);
                setQuantityError("");
              }}
              disabled={loading}
            />
            {clientWarning ? (
              <span className="field-error" role="alert">
                {clientWarning}
              </span>
            ) : null}
            {quantityError ? (
              <span className="field-error" role="alert">
                {quantityError}
              </span>
            ) : null}
          </label>

          <label className="bo-field">
            <span>Motivo (reason)</span>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value as ExitReason)}
              disabled={loading}
            >
              {(Object.keys(REASON_LABELS) as ExitReason[]).map((key) => (
                <option key={key} value={key}>
                  {REASON_LABELS[key]} ({key})
                </option>
              ))}
            </select>
          </label>

          {reason === "waste" ? (
            <label className="bo-field">
              <span>Detalle de merma (telemetría CONTEXT)</span>
              <select
                value={wasteDetail}
                onChange={(e) => setWasteDetail(e.target.value as WasteReason)}
                disabled={loading}
              >
                <option value="expired">expired</option>
                <option value="kitchen_error">kitchen_error</option>
                <option value="theft_suspected">theft_suspected</option>
              </select>
            </label>
          ) : null}

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
            {loading ? "Guardando…" : "Registrar salida"}
          </button>
        </form>
      </section>
    </>
  );
}

export default function OutboundOrderPage() {
  return (
    <RequireAuth>
      <main className="bo-shell">
        <AppNav active="inventory-outbound" />
        <section className="bo-content">
          <Suspense fallback={<p className="bo-soft">Cargando formulario…</p>}>
            <OutboundForm />
          </Suspense>
        </section>
      </main>
    </RequireAuth>
  );
}
