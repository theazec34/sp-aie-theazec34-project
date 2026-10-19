import { apiFetch } from "./api";

export type EvaluationResult = {
  section_id?: string;
  department_id?: string;
  readability?: { pass?: boolean; score?: number | null; details?: string };
  relevance?: { pass?: boolean; missing_aspects?: string[] };
  compliance?: { pass?: boolean; rule_ids?: string[]; violations?: string[] };
  overall_pass?: boolean;
  feedback_for_generator?: string;
};

export type RfpTicket = {
  ticket_id: number;
  status: string;
  original_filename: string;
  raw_pdf_path: string;
  discard_reason?: string | null;
  handoff_ready?: boolean;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  metadata?: {
    client_name?: string | null;
    location?: string | null;
    service_type?: string | null;
    scope?: string | null;
    deadline?: string | null;
    budget_range?: string | null;
    departments_needed?: string[];
    flesch_kincaid?: number | null;
    gunning_fog?: number | null;
    word_count?: number | null;
    is_rfp?: boolean;
    classifier_notes?: string | null;
    open_questions?: string[];
  } | null;
  department_sections?: Array<{
    department_id: string;
    contact_name?: string | null;
    key_aspects: string[];
    open_questions: string[];
    draft_content?: string | null;
    evaluation_results?: EvaluationResult | null;
    generation_iteration?: number;
    needs_human_review?: boolean;
    section_status?: string;
    approval_status?: string;
  }>;
  synthesizer_summary?: {
    sales_brief?: string;
    summary_lines?: string[];
    departments?: Array<{
      department_id: string;
      department_name?: string;
      contact?: string;
      ask_them?: string[];
      open_questions?: string[];
    }>;
    open_questions?: string[];
    part2?: Record<string, unknown>;
    part2_status?: string;
  } | null;
};

export async function listRfpTickets(): Promise<RfpTicket[]> {
  const res = await apiFetch("/rfp/tickets");
  if (!res.ok) throw new Error(`No se pudo listar las RFP (${res.status})`);
  return res.json();
}

export async function getRfpTicket(id: number): Promise<RfpTicket> {
  const res = await apiFetch(`/rfp/tickets/${id}`);
  if (!res.ok) throw new Error(`No se pudo obtener la RFP (${res.status})`);
  return res.json();
}

export async function uploadRfpPdf(file: File): Promise<{ ticket_id: number; status: string }> {
  const body = new FormData();
  body.append("file", file);
  const res = await apiFetch("/rfp/tickets", { method: "POST", body });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`La subida falló (${res.status}): ${text}`);
  }
  return res.json();
}

export async function startRfpGeneration(
  ticketId: number,
): Promise<{ ticket_id: number; status: string }> {
  const res = await apiFetch(`/rfp/tickets/${ticketId}/generate`, { method: "POST" });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`No se pudo iniciar la generación (${res.status}): ${text}`);
  }
  return res.json();
}
