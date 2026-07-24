"use client";

import { useCallback, useEffect, useState } from "react";
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
  IncidentSummary,
  labelFor,
} from "../../lib/incidents";

function MetricBlock({
  title,
  data,
  labels,
}: {
  title: string;
  data: Record<string, number>;
  labels: readonly { value: string; label: string }[];
}) {
  const entries = Object.entries(data).filter(([, count]) => count > 0);
  return (
    <section className="bo-panel">
      <h3>{title}</h3>
      {entries.length === 0 ? (
        <p className="bo-soft">Sin datos todavía.</p>
      ) : (
        <div className="bo-metrics" style={{ marginTop: 12 }}>
          {entries.map(([key, count]) => (
            <article key={key} className="bo-metric">
              <span className="bo-soft">{labelFor(labels, key)}</span>
              <strong>{count}</strong>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default function IncidentsSummaryPage() {
  const [summary, setSummary] = useState<IncidentSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await apiFetch("/api/incidents/summary", { skipAuth: true });
      if (!response.ok) {
        const parsed = await readApiError(response);
        throw new Error(parsed.message);
      }
      setSummary((await response.json()) as IncidentSummary);
    } catch (err) {
      setError(friendlyCatch(err, getApiBaseUrl()));
      setSummary(null);
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
        <AppNav active="incidents-summary" />
        <section className="bo-content">
          <header className="bo-topbar">
            <div>
              <p className="bo-kicker">Incidencias</p>
              <h1>Resumen ejecutivo</h1>
            </div>
            <button type="button" className="bo-btn" onClick={() => void load()} disabled={loading}>
              {loading ? "Cargando…" : "Actualizar"}
            </button>
          </header>

          {error ? (
            <div className="bo-alert bo-alert-error">
              <p>{error}</p>
              <button type="button" className="bo-btn bo-btn-small" onClick={() => void load()}>
                Reintentar
              </button>
            </div>
          ) : null}

          {loading && !summary ? <p className="bo-soft">Cargando métricas…</p> : null}

          {summary ? (
            <>
              <section className="bo-panel">
                <h3>Total de incidencias</h3>
                <p className="bo-metric">
                  <strong>{summary.total}</strong>
                </p>
              </section>
              <MetricBlock
                title="Por estado"
                data={summary.by_status}
                labels={INCIDENT_STATUSES}
              />
              <MetricBlock
                title="Por categoría"
                data={summary.by_category}
                labels={INCIDENT_CATEGORIES}
              />
              <MetricBlock
                title="Por origen"
                data={summary.by_origin}
                labels={INCIDENT_ORIGINS}
              />
              <MetricBlock
                title="Por sede"
                data={summary.by_branch}
                labels={INCIDENT_BRANCHES}
              />
            </>
          ) : null}
        </section>
      </main>
    </RequireAuth>
  );
}
