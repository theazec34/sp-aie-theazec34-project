"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import AuthenticatedShell from "../../components/AuthenticatedShell";
import {
  getRfpTicket,
  listRfpTickets,
  startRfpGeneration,
  uploadRfpPdf,
  type RfpTicket,
} from "../../lib/rfp";

const STATUS_LABEL: Record<string, string> = {
  analizando: "Analizando",
  analisis_completo: "Análisis completo",
  descartado: "Descartado",
  fallido: "Fallido",
  generando_borrador: "Generando borrador",
  en_evaluacion: "En evaluación",
  borrador_listo: "Borrador listo",
  needs_human_review: "Requiere revisión humana",
};

const POLLING = new Set([
  "analizando",
  "generando_borrador",
  "en_evaluacion",
]);

function statusLabel(status: string): string {
  return STATUS_LABEL[status] ?? status;
}

function canGenerate(status: string): boolean {
  return (
    status === "analisis_completo" ||
    status === "borrador_listo" ||
    status === "needs_human_review"
  );
}

export default function RfpIntakePage() {
  const [tickets, setTickets] = useState<RfpTicket[]>([]);
  const [selected, setSelected] = useState<RfpTicket | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [genBusy, setGenBusy] = useState(false);
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

  useEffect(() => {
    const pending = tickets.some((t) => POLLING.has(t.status));
    if (!pending) return;
    const id = window.setInterval(() => {
      void reload();
      if (selected && POLLING.has(selected.status)) {
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

  async function onGenerate() {
    if (!selected) return;
    setGenBusy(true);
    setError(null);
    try {
      await startRfpGeneration(selected.ticket_id);
      const detail = await getRfpTicket(selected.ticket_id);
      setSelected(detail);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo iniciar la generación");
    } finally {
      setGenBusy(false);
    }
  }

  return (
    <AuthenticatedShell active="rfp">
      <h1>Recepción y propuesta RFP (Marketing / Camila)</h1>
      <p className="bo-muted">
        Parte 1: sube un PDF → <code>analisis_completo</code>. Parte 2: genera
        borradores por departamento con evaluación (legibilidad, pertinencia,
        cumplimiento BRIEFING) → <code>borrador_listo</code> o{" "}
        <code>needs_human_review</code>.
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
              {canGenerate(selected.status) ? (
                <p style={{ marginTop: "0.75rem" }}>
                  <button type="button" disabled={genBusy} onClick={() => void onGenerate()}>
                    {genBusy ? "Encolando…" : "Generar borradores (Parte 2)"}
                  </button>
                </p>
              ) : null}
              {selected.status === "needs_human_review" ? (
                <p role="status">
                  Hay secciones provisionales: el límite generador↔evaluador se
                  agotó. Revisar borrador + evaluación antes de la Parte 3.
                </p>
              ) : null}
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
                  </ul>
                </div>
              ) : null}

              {selected.synthesizer_summary?.summary_lines ? (
                <div>
                  <h3>Resumen handoff Parte 1</h3>
                  <ul>
                    {selected.synthesizer_summary.summary_lines.map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {(selected.department_sections || []).length > 0 ? (
                <div>
                  <h3>Secciones por departamento</h3>
                  {selected.department_sections!.map((s) => {
                    const ev = s.evaluation_results;
                    return (
                      <div
                        key={s.department_id}
                        style={{
                          marginTop: "1rem",
                          paddingTop: "0.75rem",
                          borderTop: "1px solid #e2e8f0",
                        }}
                      >
                        <strong>
                          {s.department_id} ({s.contact_name})
                          {s.needs_human_review ? " · revisión humana" : ""}
                          {s.section_status ? ` · ${s.section_status}` : ""}
                        </strong>
                        <ul>
                          {s.key_aspects.map((a) => (
                            <li key={a}>{a}</li>
                          ))}
                        </ul>
                        {s.draft_content ? (
                          <details>
                            <summary>
                              Borrador (iteración {s.generation_iteration ?? 0})
                            </summary>
                            <pre
                              style={{
                                whiteSpace: "pre-wrap",
                                fontSize: "0.85rem",
                                maxHeight: 240,
                                overflow: "auto",
                              }}
                            >
                              {s.draft_content}
                            </pre>
                          </details>
                        ) : null}
                        {ev ? (
                          <div style={{ marginTop: "0.5rem" }}>
                            <p>
                              Evaluación global:{" "}
                              {ev.overall_pass ? "aprobada" : "no aprobada"}
                            </p>
                            <ul>
                              <li>
                                Legibilidad: {ev.readability?.pass ? "sí" : "no"}
                                {ev.readability?.score != null
                                  ? ` (score ${ev.readability.score})`
                                  : ""}
                              </li>
                              <li>
                                Pertinencia: {ev.relevance?.pass ? "sí" : "no"}
                                {(ev.relevance?.missing_aspects || []).length
                                  ? ` · faltan: ${(ev.relevance?.missing_aspects || []).join(", ")}`
                                  : ""}
                              </li>
                              <li>
                                Cumplimiento: {ev.compliance?.pass ? "sí" : "no"}
                                {(ev.compliance?.rule_ids || []).length
                                  ? ` · reglas: ${(ev.compliance?.rule_ids || []).join(", ")}`
                                  : ""}
                              </li>
                            </ul>
                            {ev.feedback_for_generator ? (
                              <p className="bo-muted">
                                Feedback al generador: {ev.feedback_for_generator}
                              </p>
                            ) : null}
                          </div>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              ) : null}
            </article>
          )}
        </section>
      </div>
    </AuthenticatedShell>
  );
}
