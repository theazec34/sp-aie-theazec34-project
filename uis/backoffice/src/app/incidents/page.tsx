"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import AppNav from "../../components/AppNav";
import RequireAuth from "../../components/RequireAuth";
import { apiFetch } from "../../lib/api";
import { getApiBaseUrl } from "../../lib/auth";
import { friendlyCatch, readApiError } from "../../lib/errors";
import {
  INCIDENT_BRANCHES,
  INCIDENT_CATEGORIES,
  INCIDENT_ORIGINS,
  INCIDENT_STATUSES,
  Incident,
  STATUS_TRANSITIONS,
  labelFor,
} from "../../lib/incidents";

export default function IncidentsPanelPage() {
  const [items, setItems] = useState<Incident[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [originFilter, setOriginFilter] = useState("");
  const [branchFilter, setBranchFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const query = useMemo(() => {
    const params = new URLSearchParams();
    if (statusFilter) params.set("status", statusFilter);
    if (originFilter) params.set("origin", originFilter);
    if (branchFilter) params.set("branch", branchFilter);
    const qs = params.toString();
    return qs ? `?${qs}` : "";
  }, [statusFilter, originFilter, branchFilter]);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await apiFetch(`/api/incidents${query}`, { skipAuth: true });
      if (!response.ok) {
        const parsed = await readApiError(response);
        throw new Error(parsed.message);
      }
      const data = (await response.json()) as Incident[];
      setItems(data);
    } catch (err) {
      setError(friendlyCatch(err, getApiBaseUrl()));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => {
    void load();
  }, [load]);

  async function changeStatus(item: Incident, nextStatus: string) {
    setMessage("");
    setError("");
    const previous = item.status;
    setItems((current) =>
      current.map((row) =>
        row.id === item.id ? { ...row, status: nextStatus } : row
      )
    );

    try {
      const response = await apiFetch(`/api/incidents/${item.id}/status`, {
        method: "PATCH",
        skipAuth: true,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus }),
      });
      if (!response.ok) {
        const parsed = await readApiError(response);
        throw new Error(parsed.message);
      }
      const updated = (await response.json()) as Incident;
      setItems((current) =>
        current.map((row) => (row.id === updated.id ? updated : row))
      );
      setMessage(`Incidencia #${updated.id} actualizada.`);
    } catch (err) {
      setItems((current) =>
        current.map((row) =>
          row.id === item.id ? { ...row, status: previous } : row
        )
      );
      setError(friendlyCatch(err, getApiBaseUrl()));
    }
  }

  return (
    <RequireAuth>
      <main className="bo-shell">
        <AppNav active="incidents" />
        <section className="bo-content">
          <header className="bo-topbar">
            <div>
              <p className="bo-kicker">Incidencias</p>
              <h1>Panel de incidencias</h1>
            </div>
            <button type="button" className="bo-btn" onClick={() => void load()} disabled={loading}>
              {loading ? "Cargando…" : "Actualizar"}
            </button>
          </header>

          <section className="bo-panel">
            <div className="bo-filters">
              <label className="bo-field">
                <span>Estado</span>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="">Todos</option>
                  {INCIDENT_STATUSES.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="bo-field">
                <span>Origen</span>
                <select
                  value={originFilter}
                  onChange={(e) => setOriginFilter(e.target.value)}
                >
                  <option value="">Todos</option>
                  {INCIDENT_ORIGINS.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="bo-field">
                <span>Sede</span>
                <select
                  value={branchFilter}
                  onChange={(e) => setBranchFilter(e.target.value)}
                >
                  <option value="">Todas</option>
                  {INCIDENT_BRANCHES.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {error ? (
              <div className="bo-alert bo-alert-error">
                <p>{error}</p>
                <button type="button" className="bo-btn bo-btn-small" onClick={() => void load()}>
                  Reintentar
                </button>
              </div>
            ) : null}
            {message ? <p className="bo-alert bo-alert-ok">{message}</p> : null}

            {loading ? <p className="bo-soft">Cargando incidencias…</p> : null}

            {!loading && items.length === 0 ? (
              <p className="bo-soft">
                No hay incidencias con estos filtros (o el listado está vacío).
              </p>
            ) : null}

            {!loading && items.length > 0 ? (
              <div className="bo-table-wrap">
                <table className="bo-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Título</th>
                      <th>Estado</th>
                      <th>Origen</th>
                      <th>Sede</th>
                      <th>Cambiar estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item) => {
                      const nexts = STATUS_TRANSITIONS[item.status] || [];
                      return (
                        <tr key={item.id}>
                          <td>{item.id}</td>
                          <td>
                            <strong>{item.title}</strong>
                            <div className="bo-soft" style={{ fontSize: "0.8rem" }}>
                              {labelFor(INCIDENT_CATEGORIES, item.category)}
                            </div>
                          </td>
                          <td>{labelFor(INCIDENT_STATUSES, item.status)}</td>
                          <td>{labelFor(INCIDENT_ORIGINS, item.origin)}</td>
                          <td>{labelFor(INCIDENT_BRANCHES, item.branch)}</td>
                          <td>
                            {nexts.length === 0 ? (
                              <span className="bo-soft">Estado final</span>
                            ) : (
                              <select
                                defaultValue=""
                                onChange={(e) => {
                                  const value = e.target.value;
                                  e.target.value = "";
                                  if (value) void changeStatus(item, value);
                                }}
                              >
                                <option value="" disabled>
                                  Elegir…
                                </option>
                                {nexts.map((status) => (
                                  <option key={status} value={status}>
                                    {labelFor(INCIDENT_STATUSES, status)}
                                  </option>
                                ))}
                              </select>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : null}
          </section>
        </section>
      </main>
    </RequireAuth>
  );
}
