"use client";

import Link from "next/link";
import { useCallback } from "react";
import AuthenticatedShell from "../../../components/AuthenticatedShell";
import { useAsyncResource } from "../../../hooks/useAsyncResource";
import {
  CATEGORY_LABELS,
  COUNTRY_LABELS,
  listIngredients,
  stockLevel,
  stockLevelLabel,
} from "../../../lib/inventory";

export default function InventoryProductsPage() {
  const loader = useCallback(() => listIngredients(), []);
  const { data, loading, error, reload } = useAsyncResource(loader);
  const items = data ?? [];

  return (
    <AuthenticatedShell active="inventory-products">
      <header className="bo-topbar">
        <div>
          <p className="bo-kicker">Inventario · Operaciones</p>
          <h1>Stock de ingredientes</h1>
        </div>
        <div className="bo-filters" style={{ margin: 0 }}>
          <Link className="bo-btn" href="/inventory/orders/inbound">
            Nueva entrada
          </Link>
          <Link className="bo-btn" href="/inventory/orders/outbound">
            Nueva salida
          </Link>
          <button type="button" className="bo-btn" onClick={() => void reload()}>
            Actualizar
          </button>
        </div>
      </header>

      <section className="bo-panel">
        <p className="bo-soft" style={{ marginBottom: 12 }}>
          Stock calculado (entradas − salidas). Umbrales visuales: vacío ≤ 0, bajo
          &lt; 10, medio &lt; 30, sano ≥ 30.
        </p>
        {loading ? <p className="bo-soft">Cargando ingredientes…</p> : null}
        {error ? (
          <div className="bo-alert bo-alert-error">
            <p>{error}</p>
            <button
              type="button"
              className="bo-btn bo-btn-small"
              onClick={() => void reload()}
            >
              Reintentar
            </button>
          </div>
        ) : null}
        {!loading && !error && items.length === 0 ? (
          <p className="bo-soft">No hay ingredientes. Ejecuta seed_inventory.py.</p>
        ) : null}
        <div className="bo-table-wrap">
          <table className="bo-table">
            <thead>
              <tr>
                <th>Ingrediente</th>
                <th>SKU</th>
                <th>Categoría</th>
                <th>País</th>
                <th>Unidad</th>
                <th>Stock actual</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const level = stockLevel(item.current_stock);
                return (
                  <tr key={item.id} className={`inv-stock-row inv-stock-${level}`}>
                    <td>
                      <strong>{item.name}</strong>
                    </td>
                    <td>{item.sku}</td>
                    <td>{CATEGORY_LABELS[item.category] || item.category}</td>
                    <td>{COUNTRY_LABELS[item.country] || item.country}</td>
                    <td>{item.unit}</td>
                    <td>
                      <span className={`bo-badge inv-badge-${level}`}>
                        {item.current_stock} · {stockLevelLabel(level)}
                      </span>
                    </td>
                    <td>
                      <div className="bo-filters" style={{ margin: 0, gap: 6 }}>
                        <Link
                          className="bo-btn bo-btn-small"
                          href={`/inventory/orders/inbound?ingredient_id=${item.id}`}
                        >
                          Entrada
                        </Link>
                        <Link
                          className="bo-btn bo-btn-small"
                          href={`/inventory/orders/outbound?ingredient_id=${item.id}`}
                        >
                          Salida
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </AuthenticatedShell>
  );
}
