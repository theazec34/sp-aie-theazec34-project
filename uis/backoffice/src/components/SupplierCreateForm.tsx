"use client";

import { FormEvent, useState } from "react";
import { apiFetch } from "../lib/api";
import { getApiBaseUrl } from "../lib/auth";
import { friendlyCatch, readApiError } from "../lib/errors";

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

type SupplierStatus = "active" | "suspended";

type FormState = {
  name: string;
  country: "Colombia" | "USA";
  categories: string[];
  rate_per_unit: string;
  currency: "COP" | "USD";
  status: SupplierStatus;
  contact_email: string;
  notes: string;
};

const emptyForm: FormState = {
  name: "",
  country: "Colombia",
  categories: ["carne"],
  rate_per_unit: "",
  currency: "COP",
  status: "active",
  contact_email: "",
  notes: "",
};

type Props = {
  onCreated: () => void | Promise<void>;
  onError: (message: string) => void;
  onMessage: (message: string) => void;
};

/**
 * Heavy create form — lazy-loaded from /proveedores so the list shell
 * can paint before this chunk arrives.
 */
export default function SupplierCreateForm({ onCreated, onError, onMessage }: Props) {
  const [form, setForm] = useState(emptyForm);

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

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    onError("");
    onMessage("");
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
        const parsed = await readApiError(response);
        throw new Error(parsed.message);
      }
      setForm({
        ...emptyForm,
        country: form.country,
        currency: form.country === "Colombia" ? "COP" : "USD",
      });
      onMessage("Proveedor registrado correctamente.");
      await onCreated();
    } catch (err) {
      onError(`Alta rechazada: ${friendlyCatch(err, getApiBaseUrl())}`);
    }
  }

  return (
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
  );
}
