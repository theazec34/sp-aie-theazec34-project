"use client";

import { FormEvent, useState } from "react";
import AppNav from "../../components/AppNav";
import RequireAuth from "../../components/RequireAuth";
import { apiFetch } from "../../lib/api";
import {
  INCIDENT_BRANCHES,
  INCIDENT_CATEGORIES,
  INCIDENT_ORIGINS,
} from "../../lib/incidents";

type FieldErrors = Record<string, string>;

const emptyForm = {
  title: "",
  description: "",
  category: "customer_complaint",
  origin: "branch",
  branch: "central",
};

export default function NuevaIncidenciaPage() {
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [message, setMessage] = useState("");

  const branchHighlighted = form.origin === "branch";

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    setFieldErrors({});
    setLoading(true);

    try {
      const response = await apiFetch("/api/incidents", {
        method: "POST",
        skipAuth: true,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        if (Array.isArray(detail.errors)) {
          const next: FieldErrors = {};
          for (const item of detail.errors) {
            if (item.field) next[item.field] = item.message || "Valor inválido";
          }
          setFieldErrors(next);
          throw new Error(detail.detail || "Revisa los campos marcados.");
        }
        if (detail.detail && typeof detail.detail === "object" && detail.detail.field) {
          setFieldErrors({ [detail.detail.field]: detail.detail.message });
          throw new Error(detail.detail.message);
        }
        throw new Error(
          typeof detail.detail === "string"
            ? detail.detail
            : "No se pudo registrar la incidencia."
        );
      }

      setForm(emptyForm);
      setMessage("Incidencia registrada correctamente.");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <RequireAuth>
      <main className="bo-shell">
        <AppNav active="incidents-new" />
        <section className="bo-content">
          <header className="bo-topbar">
            <div>
              <p className="bo-kicker">Incidencias</p>
              <h1>Registrar incidencia</h1>
            </div>
          </header>

          <section className="bo-panel" style={{ maxWidth: 640 }}>
            <p className="bo-soft" style={{ marginBottom: 16 }}>
              El estado inicial será siempre <strong>Abierta</strong>. Usa la sede
              correcta; si el origen es sede, el campo se resalta.
            </p>

            <form className="auth-form" onSubmit={onSubmit}>
              <label className="bo-field">
                <span>Título</span>
                <input
                  required
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  disabled={loading}
                />
                {fieldErrors.title ? (
                  <span className="field-error">{fieldErrors.title}</span>
                ) : null}
              </label>

              <label className="bo-field">
                <span>Descripción</span>
                <textarea
                  required
                  rows={4}
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  disabled={loading}
                />
                {fieldErrors.description ? (
                  <span className="field-error">{fieldErrors.description}</span>
                ) : null}
              </label>

              <label className="bo-field">
                <span>Categoría</span>
                <select
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  disabled={loading}
                >
                  {INCIDENT_CATEGORIES.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
                {fieldErrors.category ? (
                  <span className="field-error">{fieldErrors.category}</span>
                ) : null}
              </label>

              <label className="bo-field">
                <span>Origen</span>
                <select
                  value={form.origin}
                  onChange={(e) => setForm({ ...form, origin: e.target.value })}
                  disabled={loading}
                >
                  {INCIDENT_ORIGINS.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>

              <label
                className={`bo-field${branchHighlighted ? " branch-highlight" : ""}`}
              >
                <span>Sede (obligatoria)</span>
                <select
                  required
                  value={form.branch}
                  onChange={(e) => setForm({ ...form, branch: e.target.value })}
                  disabled={loading}
                >
                  {INCIDENT_BRANCHES.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
                {branchHighlighted ? (
                  <span className="api-base-hint">
                    Estás reportando desde una sede concreta — confirma el local.
                  </span>
                ) : null}
                {fieldErrors.branch ? (
                  <span className="field-error">{fieldErrors.branch}</span>
                ) : null}
              </label>

              {error ? <p className="bo-alert bo-alert-error">{error}</p> : null}
              {message ? <p className="bo-alert bo-alert-ok">{message}</p> : null}

              <button
                className="bo-btn bo-btn-primary"
                type="submit"
                disabled={loading}
              >
                {loading ? "Enviando…" : "Registrar incidencia"}
              </button>
            </form>
          </section>
        </section>
      </main>
    </RequireAuth>
  );
}
