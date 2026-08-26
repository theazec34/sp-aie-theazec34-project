"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import AuthenticatedShell from "../../components/AuthenticatedShell";
import { apiFetch } from "../../lib/api";
import { getApiBaseUrl } from "../../lib/auth";
import { friendlyCatch, readApiError } from "../../lib/errors";

type LocationKpi = {
  location_id: string;
  country: string;
  total_purchase_cost: number;
  total_waste_cost: number;
  waste_ratio: number;
  stockout_events_count: number;
  price_alert_events_count: number;
  currency: string;
};

type ReportPayload = {
  week_start: string;
  locations: LocationKpi[];
};

type RunMeta = {
  status: string;
  started_at: string;
  finished_at: string | null;
  rows_extracted: number;
  rows_upserted: number;
  week_start: string;
};

function money(value: number, currency: string): string {
  try {
    return new Intl.NumberFormat(currency === "USD" ? "en-US" : "es-CO", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(value);
  } catch {
    return `${value} ${currency}`;
  }
}

function weekEndLabel(weekStart: string): string {
  const start = new Date(`${weekStart}T00:00:00Z`);
  const end = new Date(start);
  end.setUTCDate(end.getUTCDate() + 6);
  return end.toISOString().slice(0, 10);
}

function KpiTable({
  title,
  description,
  rows,
  renderValue,
}: {
  title: string;
  description: string;
  rows: LocationKpi[];
  renderValue: (row: LocationKpi) => string;
}) {
  return (
    <section className="bo-panel">
      <h3>{title}</h3>
      <p className="bo-soft">{description}</p>
      <div className="bo-table-wrap">
        <table className="bo-table">
          <thead>
            <tr>
              <th>Local</th>
              <th>País</th>
              <th>Valor</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={3}>Sin datos para esta semana</td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={`${title}-${row.location_id}`}>
                  <td>{row.location_id}</td>
                  <td>{row.country}</td>
                  <td>{renderValue(row)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default function ReportingDashboardPage() {
  const [report, setReport] = useState<ReportPayload | null>(null);
  const [runMeta, setRunMeta] = useState<RunMeta | null>(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [kpiRes, runRes] = await Promise.all([
        apiFetch("/reporting/weekly-location-performance"),
        apiFetch("/reporting/pipeline-runs/latest"),
      ]);
      if (!kpiRes.ok) {
        const parsed = await readApiError(kpiRes);
        throw new Error(parsed.message);
      }
      setReport((await kpiRes.json()) as ReportPayload);
      if (runRes.ok) {
        setRunMeta((await runRes.json()) as RunMeta);
      } else {
        setRunMeta(null);
      }
    } catch (err) {
      setError(friendlyCatch(err, getApiBaseUrl()));
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const trigger = useCallback(async () => {
    setRunning(true);
    setError("");
    try {
      const response = await apiFetch("/reporting/pipeline-runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!response.ok) {
        const parsed = await readApiError(response);
        throw new Error(parsed.message);
      }
      await load();
    } catch (err) {
      setError(friendlyCatch(err, getApiBaseUrl()));
    } finally {
      setRunning(false);
    }
  }, [load]);

  useEffect(() => {
    void load();
  }, [load]);

  const rows = useMemo(() => {
    const list = report?.locations ?? [];
    return [...list].sort((a, b) =>
      a.country === b.country
        ? String(a.location_id).localeCompare(String(b.location_id))
        : a.country.localeCompare(b.country)
    );
  }, [report]);

  const periodLabel = report
    ? `${report.week_start} → ${weekEndLabel(report.week_start)} (semana ISO, UTC)`
    : null;

  return (
    <AuthenticatedShell active="reporting">
      <header className="bo-topbar">
        <div>
          <p className="bo-kicker">Reporte para Mariana (CEO) y Felipe (Ops)</p>
          <h1>Costo y merma por local</h1>
          <p className="bo-soft">
            Consolidado semanal de compra, merma, quiebres de stock y alertas de precio.
            Los montos se muestran en la moneda de cada país (sin convertir COP↔USD).
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button type="button" className="bo-btn" onClick={() => void load()} disabled={loading}>
            {loading ? "Cargando…" : "Actualizar"}
          </button>
          <button
            type="button"
            className="bo-btn"
            onClick={() => void trigger()}
            disabled={running || loading}
          >
            {running ? "Calculando…" : "Recalcular semana"}
          </button>
        </div>
      </header>

      {error ? (
        <div className="bo-alert bo-alert-error">
          <p>{error}</p>
          <button type="button" className="bo-btn bo-btn-small" onClick={() => void load()}>
            Reintentar
          </button>
        </div>
      ) : null}

      {periodLabel ? (
        <p className="bo-soft" style={{ marginBottom: 8 }}>
          Periodo: <strong>{periodLabel}</strong>
        </p>
      ) : null}

      {runMeta ? (
        <p className="bo-soft" style={{ marginBottom: 16 }}>
          Última corrida del pipeline: <strong>{runMeta.status}</strong> · extraídos{" "}
          {runMeta.rows_extracted} · locales escritos {runMeta.rows_upserted}
        </p>
      ) : null}

      {loading && !report ? <p className="bo-soft">Cargando KPIs…</p> : null}

      {report ? (
        <div className="bo-telemetry-grid">
          <KpiTable
            title="Costo de compra por local"
            description="Cuánto gastó cada local comprando ingredientes a proveedores en la semana."
            rows={rows}
            renderValue={(row) => money(row.total_purchase_cost, row.currency)}
          />
          <KpiTable
            title="Costo de merma por local"
            description="Pérdida monetaria por producto vencido, error de cocina o robo."
            rows={rows}
            renderValue={(row) => money(row.total_waste_cost, row.currency)}
          />
          <KpiTable
            title="Ratio de merma"
            description="Costo de merma como proporción del costo de compra (0 si no hubo compras)."
            rows={rows}
            renderValue={(row) => `${(row.waste_ratio * 100).toFixed(1)}%`}
          />
          <KpiTable
            title="Frecuencia de quiebre de stock"
            description="Cuántas veces el stock cayó por debajo del mínimo configurado."
            rows={rows}
            renderValue={(row) => String(row.stockout_events_count)}
          />
          <KpiTable
            title="Frecuencia de alertas de precio"
            description="Cuántas veces el costo de un ingrediente subió de forma anómala."
            rows={rows}
            renderValue={(row) => String(row.price_alert_events_count)}
          />
        </div>
      ) : null}
    </AuthenticatedShell>
  );
}
