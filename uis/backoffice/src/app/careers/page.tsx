"use client";

import { useEffect, useState } from "react";
import AuthenticatedShell from "../../components/AuthenticatedShell";
import { ApiError, apiFetch } from "../../lib/api";

type CareerRow = {
  id: number;
  name: string;
  email: string;
  phone: string;
  department: string;
  experience_years: number;
  message: string;
  cv_filename: string;
  created_at: string;
};

export default function CareersPage() {
  const [rows, setRows] = useState<CareerRow[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await apiFetch("/careers");
        if (!res.ok) {
          throw new ApiError(
            `No se pudieron cargar las candidaturas (HTTP ${res.status}). ` +
              `Comprueba la sesión e inténtalo de nuevo.`,
            res.status
          );
        }
        const data = (await res.json()) as CareerRow[];
        if (!cancelled) setRows(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Error al cargar");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <AuthenticatedShell active="careers">
      <header className="bo-topbar">
        <div>
          <p className="bo-kicker">Web pública</p>
          <h1>Candidaturas</h1>
        </div>
      </header>
      <section className="bo-panel">
        <p>
          Enviadas desde <strong>/trabaja-con-nosotros</strong>. El CV solo guarda el
          nombre de fichero en esta versión.
        </p>
        {loading ? <p>Cargando…</p> : null}
        {error ? (
          <p className="form-status form-status-error" role="alert">
            {error}
          </p>
        ) : null}
        {!loading && !error && rows.length === 0 ? <p>Aún no hay candidaturas.</p> : null}
        {rows.length > 0 ? (
          <ul className="bo-list">
            {rows.map((r) => (
              <li key={r.id} className="bo-list-item">
                <strong>
                  #{r.id} · {r.name}
                </strong>{" "}
                — {r.department} ({r.experience_years} años)
                <br />
                {r.email} · {r.phone}
                {r.cv_filename ? ` · CV: ${r.cv_filename}` : ""}
                <p>{r.message}</p>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    </AuthenticatedShell>
  );
}
