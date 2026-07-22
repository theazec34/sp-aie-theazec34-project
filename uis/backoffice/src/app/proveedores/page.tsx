"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import AppNav from "../../components/AppNav";
import RequireAuth from "../../components/RequireAuth";
import { apiFetch } from "../../lib/api";
import { getApiBaseUrl } from "../../lib/auth";

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


const emptyForm = {
  name: "",
  country: "Colombia" as "Colombia" | "USA",
  categories: ["carne"] as string[],
  rate_per_unit: "",
  currency: "COP" as "COP" | "USD",
  status: "active" as SupplierStatus,
  contact_email: "",
  notes: "",
};

export default function ProveedoresPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [countryFilter, setCountryFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [form, setForm] = useState(emptyForm);
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
        `No se pudo cargar el directorio. ¿API en ${getApiBaseUrl()}? ${(err as Error).message}`
      );
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => {
    void loadSuppliers();
  }, [loadSuppliers]);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    const payload = {
      name: form.name.trim(),
      country: form.country,
      categories: form.categories,
      rate_per_unit: Number(form.rate_per_unit),
      currency: form.country === "Colombia" ? "COP" : "USD",
      status: form.status,
      contact_email: form.contact_email.trim() || null,
      notes: form.notes.trim() || null,
    };

    try {
      const response = await apiFetch(`/suppliers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(
          typeof detail.detail === "string"
            ? detail.detail
            : JSON.stringify(detail.detail || detail)
        );
      }
      setForm({
        ...emptyForm,
        country: form.country,
        currency: form.country === "Colombia" ? "COP" : "USD",
      });
      setMessage("Proveedor registrado correctamente.");
      await loadSuppliers();
    } catch (err) {
      setError(`Alta rechazada: ${(err as Error).message}`);
    }
  }

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
        const detail = await response.json().catch(() => ({}));
        throw new Error(JSON.stringify(detail.detail || detail));
      }
      setMessage(`Tarifa del proveedor #${id} actualizada.`);
      await loadSuppliers();
    } catch (err) {
      setError(`No se pudo actualizar la tarifa: ${(err as Error).message}`);
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
        throw new Error(`HTTP ${response.status}`);
      }
      setMessage(`Estado de ${supplier.name} → ${next}.`);
      await loadSuppliers();
    } catch (err) {
      setError(`No se pudo cambiar el estado: ${(err as Error).message}`);
    }
  }

  function onCountryChange(country: "Colombia" | "USA") {
    setForm((prev) => ({
      ...prev,
      country,
      currency: country === "Colombia" ? "COP" : "USD",
    }));
  }

  function toggleCategory(category: string) {
    setForm((prev) => {
      const exists = prev.categories.includes(category);
      const categories = exists
        ? prev.categories.filter((item) => item !== category)
        : [...prev.categories, category];
      return { ...prev, categories: categories.length ? categories : prev.categories };
    });
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
          {error ? <p className="bo-alert bo-alert-error">{error}</p> : null}
          {message ? <p className="bo-alert bo-alert-ok">{message}</p> : null}
        </section>

        <section className="bo-panel">
          <h2>Listado ({suppliers.length})</h2>
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

        <section className="bo-panel">
          <h2>Registrar proveedor</h2>
          <form className="bo-form" onSubmit={handleCreate}>
            <label className="bo-field">
              <span>Nombre</span>
              <input
                required
                value={form.name}
                onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
              />
            </label>
            <label className="bo-field">
              <span>País</span>
              <select
                value={form.country}
                onChange={(event) =>
                  onCountryChange(event.target.value as "Colombia" | "USA")
                }
              >
                <option value="Colombia">Colombia</option>
                <option value="USA">USA</option>
              </select>
            </label>
            <label className="bo-field">
              <span>Moneda (auto)</span>
              <input value={form.currency} readOnly />
            </label>
            <label className="bo-field">
              <span>Tarifa por unidad</span>
              <input
                required
                type="number"
                min="0.01"
                step="0.01"
                value={form.rate_per_unit}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, rate_per_unit: event.target.value }))
                }
              />
            </label>
            <label className="bo-field">
              <span>Estado</span>
              <select
                value={form.status}
                onChange={(event) =>
                  setForm((prev) => ({
                    ...prev,
                    status: event.target.value as SupplierStatus,
                  }))
                }
              >
                <option value="active">active</option>
                <option value="suspended">suspended</option>
              </select>
            </label>
            <label className="bo-field">
              <span>Email de contacto</span>
              <input
                type="email"
                value={form.contact_email}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, contact_email: event.target.value }))
                }
              />
            </label>
            <fieldset className="bo-fieldset">
              <legend>Categorías</legend>
              <div className="bo-chips">
                {CATEGORIES.map((category) => (
                  <label key={category} className="bo-chip">
                    <input
                      type="checkbox"
                      checked={form.categories.includes(category)}
                      onChange={() => toggleCategory(category)}
                    />
                    {category}
                  </label>
                ))}
              </div>
            </fieldset>
            <label className="bo-field bo-field-wide">
              <span>Notas</span>
              <textarea
                rows={3}
                value={form.notes}
                onChange={(event) => setForm((prev) => ({ ...prev, notes: event.target.value }))}
              />
            </label>
            <button type="submit" className="bo-btn bo-btn-primary">
              Crear proveedor
            </button>
          </form>
        </section>
      </section>
    </main>
    </RequireAuth>
  );
}
