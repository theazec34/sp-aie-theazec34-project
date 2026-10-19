"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import AuthenticatedShell from "../../components/AuthenticatedShell";
import {
  getRfpTicket,
  listRfpTickets,
  uploadRfpPdf,
  type RfpTicket,
} from "../../lib/rfp";

const STATUS_LABEL: Record<string, string> = {
  analizando: "Analizando",
  analisis_completo: "Análisis completo",
  descartado: "Descartado",
  fallido: "Fallido",
};

function statusLabel(status: string): string {
  return STATUS_LABEL[status] ?? status;
}

export default function RfpIntakePage() {
  const [tickets, setTickets] = useState<RfpTicket[]>([]);
  const [selected, setSelected] = useState<RfpTicket | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  const reload = useCallback(async () => {
    try {
      const rows = await listRfpTickets();
      setTickets(rows);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al listar tickets");
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  // Poll mientras haya tickets en análisis
  useEffect(() => {
    const pending = tickets.some((t) => t.status === "analizando");
    if (!pending) return;
    const id = window.setInterval(() => {
      void reload();
      if (selected?.status === "analizando") {
        void getRfpTicket(selected.ticket_id).then(setSelected).catch(() => undefined);
      }
    }, 2000);
    return () => window.clearInterval(id);
  }, [tickets, selected, reload]);

  async function onUpload(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const accepted = await uploadRfpPdf(file);
      await reload();
      const detail = await getRfpTicket(accepted.ticket_id);
      setSelected(detail);
      setFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "La subida falló");
    } finally {
      setBusy(false);
    }
  }

  async function openTicket(id: number) {
    try {
      setSelected(await getRfpTicket(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cargar el ticket");
    }
  }

  return (
    <AuthenticatedShell active="rfp">
      <h1>Recepción de RFP (Marketing / Camila)</h1>
      <p className="bo-muted">
        Sube un PDF de solicitud de propuesta. El ticket pasa por{" "}
        <code>analizando</code> → <code>analisis_completo</code>,{" "}
        <code>descartado</code> o <code>fallido</code>. El análisis corre en
        segundo plano.
      </p>

      <form onSubmit={onUpload} className="bo-card" style={{ marginBottom: "1.5rem" }}>
        <label>
          PDF de RFP
          <input
            type="file"
            accept=".pdf,.md,.txt"
            onChange={(ev) => setFile(ev.target.files?.[0] ?? null)}
          />
        </label>
        <button type="submit" disabled={!file || busy}>
          {busy ? "Subiendo…" : "Crear ticket"}
        </button>
      </form>

      {error ? <p role="alert">{error}</p> : null}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.4fr", gap: "1.25rem" }}>
        <section>
          <h2>Tickets</h2>
          <ul className="bo-list">
            {tickets.map((t) => (
              <li key={t.ticket_id}>
                <button type="button" onClick={() => void openTicket(t.ticket_id)}>
                  #{t.ticket_id} · {statusLabel(t.status)} · {t.original_filename}
                </button>
              </li>
            ))}
            {tickets.length === 0 ? <li>Sin tickets aún.</li> : null}
          </ul>
        </section>

        <section>
          <h2>Detalle</h2>
          {!selected ? (
            <p className="bo-muted">Selecciona un ticket.</p>
          ) : (
            <article className="bo-card">
              <p>
                <strong>#{selected.ticket_id}</strong> — {statusLabel(selected.status)}
              </p>
              {selected.discard_reason ? (
                <p role="status">Descartado: {selected.discard_reason}</p>
              ) : null}
              {selected.error_message ? (
                <p role="alert">Fallo: {selected.error_message.slice(0, 240)}</p>
              ) : null}
              {selected.metadata ? (
                <div>
                  <h3>Metadatos</h3>
                  <ul>
                    <li>Cliente: {selected.metadata.client_name || "—"}</li>
                    <li>Ubicación: {selected.metadata.location || "—"}</li>
                    <li>Servicio: {selected.metadata.service_type || "—"}</li>
                    <li>Alcance: {selected.metadata.scope || "—"}</li>
                    <li>Fecha límite: {selected.metadata.deadline || "—"}</li>
                    <li>Presupuesto: {selected.metadata.budget_range || "—"}</li>
                    <li>
                      Departamentos:{" "}
                      {(selected.metadata.departments_needed || []).join(", ") || "—"}
                    </li>
                    <li>
                      Legibilidad FK/Fog: {selected.metadata.flesch_kincaid ?? "—"} /{" "}
                      {selected.metadata.gunning_fog ?? "—"} (palabras{" "}
                      {selected.metadata.word_count ?? "—"})
                    </li>
                    {selected.metadata.classifier_notes ? (
                      <li>Clasificador: {selected.metadata.classifier_notes}</li>
                    ) : null}
                  </ul>
                </div>
              ) : null}

              {selected.synthesizer_summary ? (
                <div>
                  <h3>Qué pedir a quién (Marketing / Ventas)</h3>
                  <p>{selected.synthesizer_summary.sales_brief}</p>
                  <ul>
                    {(selected.synthesizer_summary.summary_lines || []).map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                  {(selected.synthesizer_summary.departments || []).map((d) => (
                    <div key={d.department_id} style={{ marginTop: "0.75rem" }}>
                      <strong>
                        {d.department_name || d.department_id} — {d.contact}
                      </strong>
                      <ul>
                        {(d.ask_them || []).map((a) => (
                          <li key={a}>{a}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : null}

              {(selected.department_sections || []).length > 0 ? (
                <div>
                  <h3>Aspectos clave por departamento</h3>
                  {selected.department_sections!.map((s) => (
                    <div key={s.department_id}>
                      <strong>
                        {s.department_id} ({s.contact_name})
                      </strong>
                      <ul>
                        {s.key_aspects.map((a) => (
                          <li key={a}>{a}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : null}
            </article>
          )}
        </section>
      </div>
    </AuthenticatedShell>
  );
}
