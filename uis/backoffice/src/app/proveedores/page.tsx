"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useState } from "react";
import AppNav from "../../components/AppNav";
import RequireAuth from "../../components/RequireAuth";
import { apiFetch } from "../../lib/api";
import { getApiBaseUrl } from "../../lib/auth";
import { friendlyCatch, readApiError } from "../../lib/errors";

type SupplierStatus = "active" | "suspended";

type Supplier = {
  id: number;
  name: string;
  country: "Colombia" | "USA";
  categories: string[];
  rate_per_unit: number;
  currency: "COP" | "USD";
  status: SupplierStatus;
  contact_email?: string | null;
  notes?: string | null;
  updated_at: string;
};

const CATEGORIES = [
  "carne",
  "verduras_y_hortalizas",
  "salsas_y_condimentos",
  "bebidas",
  "packaging",
  "productos_limpieza",
  "lacteos",
  "carbon_y_combustible",
] as const;

const SupplierCreateForm = dynamic(
  () => import("../../components/SupplierCreateForm"),
  {
    loading: () => (
      <section className="bo-panel" aria-busy="true">
        <p className="bo-soft">Cargando formulario de alta…</p>
      </section>
    ),
    ssr: false,
  }
);

export default function ProveedoresPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [countryFilter, setCountryFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [rateDrafts, setRateDrafts] = useState<Record<number, string>>({});

  const query = useMemo(() => {
    const params = new URLSearchParams();
    if (countryFilter) params.set("country", countryFilter);
    if (categoryFilter) params.set("category", categoryFilter);
    const qs = params.toString();
    return qs ? `?${qs}` : "";
  }, [countryFilter, categoryFilter]);

  const loadSuppliers = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await apiFetch(`/suppliers${query}`);
      if (!response.ok) {
        throw new Error(`Error HTTP ${response.status}`);
      }
      const data = (await response.json()) as Supplier[];
      setSuppliers(data);
      const drafts: Record<number, string> = {};
      for (const item of data) {
        drafts[item.id] = String(item.rate_per_unit);
      }
      setRateDrafts(drafts);
    } catch (err) {
      setError(
        `No se pudo cargar el directorio. ${friendlyCatch(err, getApiBaseUrl())}`
      );
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => {
    void loadSuppliers();
  }, [loadSuppliers]);

  async function updateRate(id: number) {
    setError("");
    setMessage("");
    const rate = Number(rateDrafts[id]);
    try {
      const response = await apiFetch(`/suppliers/${id}/rate`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rate_per_unit: rate }),
      });
      if (!response.ok) {
        const parsed = await readApiError(response);
        throw new Error(parsed.message);
      }
      setMessage(`Tarifa del proveedor #${id} actualizada.`);
      await loadSuppliers();
    } catch (err) {
      setError(`No se pudo actualizar la tarifa: ${friendlyCatch(err, getApiBaseUrl())}`);
    }
  }

  async function toggleStatus(supplier: Supplier) {
    setError("");
    setMessage("");
    const next = supplier.status === "active" ? "suspended" : "active";
    try {
      const response = await apiFetch(`/suppliers/${supplier.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: next }),
      });
      if (!response.ok) {
        const parsed = await readApiError(response);
        throw new Error(parsed.message);
      }
      setMessage(`Estado de ${supplier.name} → ${next}.`);
      await loadSuppliers();
    } catch (err) {
      setError(`No se pudo cambiar el estado: ${friendlyCatch(err, getApiBaseUrl())}`);
    }
  }

  return (
    <RequireAuth>
    <main className="bo-shell">
      <AppNav active="proveedores" />

      <section className="bo-content">
        <header className="bo-topbar">
          <div>
            <p className="bo-kicker">Compras · Lucía Fernández</p>
            <h1>Directorio de proveedores</h1>
          </div>
          <span className="bo-status">Fuente única · TinyDB</span>
        </header>

        <section className="bo-panel">
          <div className="bo-filters">
            <label>
              País
              <select
                value={countryFilter}
                onChange={(event) => setCountryFilter(event.target.value)}
              >
                <option value="">Todos</option>
                <option value="Colombia">Colombia</option>
                <option value="USA">USA</option>
              </select>
            </label>
            <label>
              Categoría
              <select
                value={categoryFilter}
                onChange={(event) => setCategoryFilter(event.target.value)}
              >
                <option value="">Todas</option>
                {CATEGORIES.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" className="bo-btn" onClick={() => void loadSuppliers()}>
              Actualizar
            </button>
          </div>
          {loading ? <p className="bo-soft">Cargando…</p> : null}
          {error ? (
            <div className="bo-alert bo-alert-error">
              <p>{error}</p>
              <button
                type="button"
                className="bo-btn bo-btn-small"
                onClick={() => void loadSuppliers()}
              >
                Reintentar
              </button>
            </div>
          ) : null}
          {message ? <p className="bo-alert bo-alert-ok">{message}</p> : null}
        </section>

        <section className="bo-panel">
          <h2>Listado ({suppliers.length})</h2>
          {!loading && !error && suppliers.length === 0 ? (
            <p className="bo-soft">No hay proveedores con estos filtros.</p>
          ) : null}
          <div className="bo-table-wrap">
            <table className="bo-table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>País</th>
                  <th>Categorías</th>
                  <th>Tarifa</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {suppliers.map((supplier) => (
                  <tr key={supplier.id}>
                    <td>
                      <strong>{supplier.name}</strong>
                      <div className="bo-soft">
                        act. {new Date(supplier.updated_at).toLocaleString()}
                      </div>
                    </td>
                    <td>{supplier.country}</td>
                    <td>{supplier.categories.join(", ")}</td>
                    <td>
                      <div className="bo-inline">
                        <input
                          className="bo-rate-input"
                          value={rateDrafts[supplier.id] ?? ""}
                          onChange={(event) =>
                            setRateDrafts((prev) => ({
                              ...prev,
                              [supplier.id]: event.target.value,
                            }))
                          }
                        />
                        <span>{supplier.currency}</span>
                        <button
                          type="button"
                          className="bo-btn bo-btn-small"
                          onClick={() => void updateRate(supplier.id)}
                        >
                          Guardar
                        </button>
                      </div>
                    </td>
                    <td>
                      <span
                        className={
                          supplier.status === "active"
                            ? "bo-badge bo-badge-active"
                            : "bo-badge bo-badge-suspended"
                        }
                      >
                        {supplier.status}
                      </span>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="bo-btn bo-btn-small"
                        onClick={() => void toggleStatus(supplier)}
                      >
                        {supplier.status === "active" ? "Suspender" : "Activar"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <SupplierCreateForm
          onCreated={loadSuppliers}
          onError={setError}
          onMessage={setMessage}
        />
      </section>
    </main>
    </RequireAuth>
  );
}
