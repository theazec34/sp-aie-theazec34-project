"use client";

import { useCallback, useEffect, useState } from "react";
import AuthenticatedShell from "../../components/AuthenticatedShell";
import { apiFetch } from "../../lib/api";
import { getApiBaseUrl } from "../../lib/auth";
import { friendlyCatch, readApiError } from "../../lib/errors";

type ReportResponse = {
  period: { from: string; to: string };
  metrics: {
    events_per_day: Array<{ date: string; count: number }>;
    error_rate_by_type: Array<{
      date: string;
      event_type: string;
      error_count: number;
      daily_total: number;
      rate: number;
    }>;
    auth_failure_rate: Array<{
      date: string;
      failed: number;
      succeeded: number;
      attempts: number;
      rate: number;
    }>;
    latency_by_route: Array<{
      date: string;
      route: string;
      avg_duration_ms: number;
      samples: number;
    }>;
  };
};

function BarChart({
  rows,
  labelKey,
  valueKey,
}: {
  rows: Array<Record<string, string | number>>;
  labelKey: string;
  valueKey: string;
}) {
  const max = Math.max(1, ...rows.map((r) => Number(r[valueKey]) || 0));
  if (rows.length === 0) {
    return <p className="bo-soft">Sin datos en el periodo.</p>;
  }
  return (
    <ul className="bo-telemetry-bars" aria-label="Gráfico de barras">
      {rows.map((row) => {
        const value = Number(row[valueKey]) || 0;
        const pct = Math.round((value / max) * 100);
        return (
          <li key={String(row[labelKey])}>
            <span className="bo-telemetry-bar-label">{String(row[labelKey])}</span>
            <span className="bo-telemetry-bar-track">
              <span className="bo-telemetry-bar-fill" style={{ width: `${pct}%` }} />
            </span>
            <span className="bo-telemetry-bar-value">{value}</span>
          </li>
        );
      })}
    </ul>
  );
}

export default function TelemetryReportPage() {
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await apiFetch("/telemetry/report");
      if (!response.ok) {
        const parsed = await readApiError(response);
        throw new Error(parsed.message);
      }
      setReport((await response.json()) as ReportResponse);
    } catch (err) {
      setError(friendlyCatch(err, getApiBaseUrl()));
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <AuthenticatedShell active="telemetry">
      <header className="bo-topbar">
        <div>
          <p className="bo-kicker">Telemetría</p>
          <h1>Reporte técnico</h1>
          <p className="bo-soft">
            Radar operativo para ingeniería (volumen, errores, auth, latencia). No es un
            dashboard de negocio.
          </p>
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

      {report ? (
        <p className="bo-soft" style={{ marginBottom: 16 }}>
          Periodo: <strong>{report.period.from}</strong> → <strong>{report.period.to}</strong>{" "}
          (UTC)
        </p>
      ) : null}

      {loading && !report ? <p className="bo-soft">Cargando métricas…</p> : null}

      {report ? (
        <div className="bo-telemetry-grid">
          <section className="bo-panel">
            <h3>Eventos por día</h3>
            <p className="bo-soft">¿Cuántos eventos llegan por día?</p>
            <BarChart
              rows={report.metrics.events_per_day}
              labelKey="date"
              valueKey="count"
            />
          </section>

          <section className="bo-panel">
            <h3>Tasa de error por tipo</h3>
            <p className="bo-soft">¿Qué proporción del tráfico diario es cada error técnico?</p>
            <div className="bo-table-wrap">
              <table className="bo-table">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Tipo</th>
                    <th>Errores</th>
                    <th>Total día</th>
                    <th>Tasa</th>
                  </tr>
                </thead>
                <tbody>
                  {report.metrics.error_rate_by_type.length === 0 ? (
                    <tr>
                      <td colSpan={5}>Sin errores en el periodo</td>
                    </tr>
                  ) : (
                    report.metrics.error_rate_by_type.map((row) => (
                      <tr key={`${row.date}-${row.event_type}`}>
                        <td>{row.date}</td>
                        <td>
                          <code>{row.event_type}</code>
                        </td>
                        <td>{row.error_count}</td>
                        <td>{row.daily_total}</td>
                        <td>{(row.rate * 100).toFixed(1)}%</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="bo-panel">
            <h3>Tasa de fallo de login</h3>
            <p className="bo-soft">¿Qué % de intentos de login fallan cada día?</p>
            <div className="bo-table-wrap">
              <table className="bo-table">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Fallidos</th>
                    <th>OK</th>
                    <th>Intentos</th>
                    <th>Tasa</th>
                  </tr>
                </thead>
                <tbody>
                  {report.metrics.auth_failure_rate.length === 0 ? (
                    <tr>
                      <td colSpan={5}>Sin eventos de auth en el periodo</td>
                    </tr>
                  ) : (
                    report.metrics.auth_failure_rate.map((row) => (
                      <tr key={row.date}>
                        <td>{row.date}</td>
                        <td>{row.failed}</td>
                        <td>{row.succeeded}</td>
                        <td>{row.attempts}</td>
                        <td>{(row.rate * 100).toFixed(1)}%</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="bo-panel">
            <h3>Latencia media por ruta</h3>
            <p className="bo-soft">¿Cuál es la latencia media diaria por endpoint?</p>
            <div className="bo-table-wrap">
              <table className="bo-table">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Ruta</th>
                    <th>Promedio (ms)</th>
                    <th>Muestras</th>
                  </tr>
                </thead>
                <tbody>
                  {report.metrics.latency_by_route.length === 0 ? (
                    <tr>
                      <td colSpan={4}>Sin muestras de latencia</td>
                    </tr>
                  ) : (
                    report.metrics.latency_by_route.map((row) => (
                      <tr key={`${row.date}-${row.route}`}>
                        <td>{row.date}</td>
                        <td>
                          <code>{row.route}</code>
                        </td>
                        <td>{row.avg_duration_ms}</td>
                        <td>{row.samples}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      ) : null}
    </AuthenticatedShell>
  );
}
