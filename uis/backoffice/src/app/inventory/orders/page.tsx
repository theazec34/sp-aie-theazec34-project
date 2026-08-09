"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import AppNav from "../../../components/AppNav";
import RequireAuth from "../../../components/RequireAuth";
import { getApiBaseUrl } from "../../../lib/auth";
import { friendlyCatch } from "../../../lib/errors";
import {
  InventoryOrder,
  listOrders,
  REASON_LABELS,
} from "../../../lib/inventory";

export default function InventoryOrdersPage() {
  const [orders, setOrders] = useState<InventoryOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await listOrders();
      setOrders(data);
    } catch (err) {
      setError(friendlyCatch(err, getApiBaseUrl()));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <RequireAuth>
      <main className="bo-shell">
        <AppNav active="inventory-orders" />
        <section className="bo-content">
          <header className="bo-topbar">
            <div>
              <p className="bo-kicker">Inventario · solo lectura</p>
              <h1>Historial de órdenes</h1>
            </div>
            <div className="bo-filters" style={{ margin: 0 }}>
              <Link className="bo-btn" href="/inventory/products">
                Stock
              </Link>
              <button type="button" className="bo-btn" onClick={() => void load()}>
                Actualizar
              </button>
            </div>
          </header>

          <section className="bo-panel">
            <p className="bo-soft" style={{ marginBottom: 12 }}>
              Entradas (IngredientEntry) y salidas (IngredientExit).{" "}
              <code>user_uuid</code> es el id numérico TinyDB del autor (string).
            </p>
            {loading ? <p className="bo-soft">Cargando historial…</p> : null}
            {error ? (
              <div className="bo-alert bo-alert-error">
                <p>{error}</p>
                <button
                  type="button"
                  className="bo-btn bo-btn-small"
                  onClick={() => void load()}
                >
                  Reintentar
                </button>
              </div>
            ) : null}
            {!loading && !error && orders.length === 0 ? (
              <p className="bo-soft">No hay órdenes registradas.</p>
            ) : null}
            <div className="bo-table-wrap">
              <table className="bo-table">
                <thead>
                  <tr>
                    <th>Tipo</th>
                    <th>Ingrediente</th>
                    <th>Cantidad</th>
                    <th>Detalle</th>
                    <th>Local</th>
                    <th>Fecha</th>
                    <th>user_uuid</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => {
                    const inbound = order.kind === "inbound";
                    return (
                      <tr key={`${order.kind}-${order.id}`}>
                        <td>
                          <span
                            className={`bo-badge ${
                              inbound ? "inv-badge-inbound" : "inv-badge-outbound"
                            }`}
                          >
                            {inbound ? "Entrada" : "Salida"}
                          </span>
                        </td>
                        <td>
                          <strong>{order.ingredient.name}</strong>
                          <div className="bo-soft">{order.ingredient.sku}</div>
                        </td>
                        <td>
                          {order.quantity} {order.ingredient.unit}
                        </td>
                        <td>
                          {inbound
                            ? order.supplier_name || "—"
                            : order.reason
                              ? REASON_LABELS[
                                  order.reason as keyof typeof REASON_LABELS
                                ] || order.reason
                              : "—"}
                        </td>
                        <td>{order.location_id}</td>
                        <td>{new Date(order.created_at).toLocaleString()}</td>
                        <td>
                          <code>{order.user_uuid}</code>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </section>
      </main>
    </RequireAuth>
  );
}
