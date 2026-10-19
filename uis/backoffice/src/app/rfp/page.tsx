"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import AuthenticatedShell from "../../components/AuthenticatedShell";
import {
  decideRfpApproval,
  getRfpTicket,
  listRfpTickets,
  startRfpApprovals,
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
  esperando_aprobacion: "Esperando aprobación",
  terminado: "Terminado",
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

function canStartApproval(status: string): boolean {
  return status === "borrador_listo" || status === "needs_human_review";
}

export default function RfpIntakePage() {
  const [tickets, setTickets] = useState<RfpTicket[]>([]);
  const [selected, setSelected] = useState<RfpTicket | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [genBusy, setGenBusy] = useState(false);
  const [apprBusy, setApprBusy] = useState<string | null>(null);
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
      setSelected(await getRfpTicket(accepted.ticket_id));
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
      setSelected(await getRfpTicket(selected.ticket_id));
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo iniciar la generación");
    } finally {
      setGenBusy(false);
    }
  }

  async function onStartApprovals() {
    if (!selected) return;
    setApprBusy("start");
    setError(null);
    try {
      await startRfpApprovals(selected.ticket_id);
      setSelected(await getRfpTicket(selected.ticket_id));
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo iniciar la aprobación");
    } finally {
      setApprBusy(null);
    }
  }

  async function onDecide(
    departmentId: string,
    action: "approve" | "reject" | "request_changes",
  ) {
    if (!selected) return;
    setApprBusy(`${departmentId}:${action}`);
    setError(null);
    try {
      await decideRfpApproval(selected.ticket_id, departmentId, action);
      setSelected(await getRfpTicket(selected.ticket_id));
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo registrar la decisión");
    } finally {
      setApprBusy(null);
    }
  }

  return (
    <AuthenticatedShell active="rfp">
      <h1>RFP Brasaland (Partes 1–3)</h1>
      <p className="bo-muted">
        Recepción → borradores evaluados → aprobación humana por departamento (en
        paralelo) → documento final. Moneda de propuesta: <strong>euros (€)</strong>.
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
                <p>
                  <button type="button" disabled={genBusy} onClick={() => void onGenerate()}>
                    {genBusy ? "Encolando…" : "Generar borradores (Parte 2)"}
                  </button>
                </p>
              ) : null}
              {canStartApproval(selected.status) ? (
                <p>
                  <button
                    type="button"
                    disabled={apprBusy !== null}
                    onClick={() => void onStartApprovals()}
                  >
                    {apprBusy === "start"
                      ? "Iniciando…"
                      : "Iniciar aprobación humana (Parte 3)"}
                  </button>
                </p>
              ) : null}

              {selected.status === "esperando_aprobacion" ? (
                <div>
                  <h3>Aprobaciones pendientes (paralelas)</h3>
                  <p className="bo-muted">
                    Cada departamento aprueba sin bloquear a los demás. Umbral CEO:
                    50.000 €/año.
                  </p>
                  {(selected.pending_approvals || []).map((p) => (
                    <div key={p.department_id} style={{ marginTop: "0.75rem" }}>
                      <strong>
                        {p.department_id} — {p.approver || "responsable"}
                      </strong>
                      <div style={{ display: "flex", gap: 8, marginTop: 6, flexWrap: "wrap" }}>
                        <button
                          type="button"
                          disabled={apprBusy !== null}
                          onClick={() => void onDecide(p.department_id, "approve")}
                        >
                          Aprobar
                        </button>
                        <button
                          type="button"
                          disabled={apprBusy !== null}
                          onClick={() => void onDecide(p.department_id, "request_changes")}
                        >
                          Pedir cambios
                        </button>
                        <button
                          type="button"
                          disabled={apprBusy !== null}
                          onClick={() => void onDecide(p.department_id, "reject")}
                        >
                          Rechazar
                        </button>
                      </div>
                    </div>
                  ))}
                  {(selected.department_sections || [])
                    .filter((s) => s.approval_status !== "aprobado")
                    .length === 0 &&
                  !(selected.pending_approvals || []).some((p) => p.department_id === "ceo")
                    ? null
                    : null}
                </div>
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
                    <li>Presupuesto (€): {selected.metadata.budget_range || "—"}</li>
                    <li>Fecha límite: {selected.metadata.deadline || "—"}</li>
                  </ul>
                </div>
              ) : null}

              {(selected.department_sections || []).map((s) => (
                <div
                  key={s.department_id}
                  style={{ marginTop: "1rem", borderTop: "1px solid #e2e8f0", paddingTop: 8 }}
                >
                  <strong>
                    {s.department_id} ({s.contact_name}) · aprobación:{" "}
                    {s.approval_status}
                  </strong>
                  {s.draft_content ? (
                    <details>
                      <summary>Borrador</summary>
                      <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.85rem" }}>
                        {s.draft_content}
                      </pre>
                    </details>
                  ) : null}
                  {s.evaluation_results ? (
                    <p className="bo-muted">
                      Eval: {s.evaluation_results.overall_pass ? "aprobada" : "no aprobada"}
                    </p>
                  ) : null}
                </div>
              ))}

              {selected.final_document ? (
                <div style={{ marginTop: "1.25rem" }}>
                  <h3>Documento final ({selected.final_document.currency_symbol || "€"})</h3>
                  <p>{selected.final_document.title}</p>
                  <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.85rem", maxHeight: 360, overflow: "auto" }}>
                    {selected.final_document.content}
                  </pre>
                </div>
              ) : null}
            </article>
          )}
        </section>
      </div>
    </AuthenticatedShell>
  );
}
