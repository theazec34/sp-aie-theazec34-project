"use client";

import { useEffect, useState } from "react";
import AuthenticatedShell from "../../components/AuthenticatedShell";
import { ApiError, apiFetch } from "../../lib/api";

type ReservationRow = {
  id: number;
  full_name: string;
  phone: string;
  email: string;
  date: string;
  time: string;
  guests: number;
  notes: string;
  status: string;
  created_at: string;
};

export default function WebReservationsPage() {
  const [rows, setRows] = useState<ReservationRow[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await apiFetch("/reservations");
        if (!res.ok) throw new ApiError("No se pudieron cargar las reservas", res.status);
        const data = (await res.json()) as ReservationRow[];
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
    <AuthenticatedShell active="web-reservations">
      <header className="bo-topbar">
        <div>
          <p className="bo-kicker">Web pública</p>
          <h1>Solicitudes de reserva</h1>
        </div>
      </header>
      <section className="bo-panel">
        <p>
          Solicitudes enviadas desde <strong>/reservas</strong> (estado «received» =
          registradas, no confirmadas automáticamente).
        </p>
        {loading ? <p>Cargando…</p> : null}
        {error ? (
          <p className="form-status form-status-error" role="alert">
            {error}
          </p>
        ) : null}
        {!loading && !error && rows.length === 0 ? (
          <p>Aún no hay solicitudes.</p>
        ) : null}
        {rows.length > 0 ? (
          <div className="bo-table-wrap">
            <table className="bo-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Nombre</th>
                  <th>Fecha</th>
                  <th>Hora</th>
                  <th>Comensales</th>
                  <th>Estado</th>
                  <th>Contacto</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td>{r.id}</td>
                    <td>{r.full_name}</td>
                    <td>{r.date}</td>
                    <td>{String(r.time).slice(0, 5)}</td>
                    <td>{r.guests}</td>
                    <td>{r.status}</td>
                    <td>
                      {r.email}
                      <br />
                      {r.phone}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </AuthenticatedShell>
  );
}
