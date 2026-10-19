import { apiFetch } from "./api";

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
  } | null;
};

export async function listRfpTickets(): Promise<RfpTicket[]> {
  const res = await apiFetch("/rfp/tickets");
  if (!res.ok) throw new Error(`List RFP failed (${res.status})`);
  return res.json();
}

export async function getRfpTicket(id: number): Promise<RfpTicket> {
  const res = await apiFetch(`/rfp/tickets/${id}`);
  if (!res.ok) throw new Error(`Get RFP failed (${res.status})`);
  return res.json();
}

export async function uploadRfpPdf(file: File): Promise<{ ticket_id: number; status: string }> {
  const body = new FormData();
  body.append("file", file);
  const res = await apiFetch("/rfp/tickets", { method: "POST", body });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Upload failed (${res.status}): ${text}`);
  }
  return res.json();
}
