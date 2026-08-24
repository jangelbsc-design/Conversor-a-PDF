/**
 * Cliente HTTP tipado para la API de PDF Suite Local.
 * Todas las llamadas van a http://localhost:8000 — sin vendor externo.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* silencio */
    }
    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

// ── Tipos ─────────────────────────────────────────────────────────

export interface DocumentWarning {
  type: string;
  message: string;
  severity: "info" | "warning" | "error";
}

export interface Document {
  id: string;
  filename_safe: string;
  original_filename: string;
  mime_type: string | null;
  sha256: string;
  size_bytes: number | null;
  page_count: number | null;
  is_encrypted: boolean;
  has_forms: boolean;
  has_signatures: boolean;
  warnings: DocumentWarning[];
  created_at: string;
  expires_at: string | null;
  deleted_at: string | null;
}

export interface Operation {
  id: string;
  doc_id: string | null;
  operation_type: string;
  status: "pending" | "running" | "success" | "failed";
  output_path: string | null;
  output_sha256: string | null;
  params_json: Record<string, unknown> | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  event_type: string;
  doc_id: string | null;
  operation_id: string | null;
  details: Record<string, unknown>;
  sha256_before: string | null;
  sha256_after: string | null;
  actor: string;
}

// ── API Functions ─────────────────────────────────────────────────

export const api = {
  // Documentos
  documents: {
    list: () => apiFetch<{ documents: Document[]; total: number }>("/api/documents/"),
    get: (id: string) => apiFetch<Document>(`/api/documents/${id}`),
    delete: (id: string) =>
      fetch(`${API_BASE}/api/documents/${id}`, { method: "DELETE" }),
    uploadUrl: () => `${API_BASE}/api/documents/upload`,
    downloadUrl: (id: string) => `${API_BASE}/api/documents/${id}/download`,
  },

  // Operaciones
  merge: (docIds: string[]) =>
    apiFetch<Operation>("/api/merge/", {
      method: "POST",
      body: JSON.stringify({ doc_ids: docIds }),
    }),

  split: (docId: string, pageRanges?: number[][], splitAll?: boolean) =>
    apiFetch<Operation>("/api/split/", {
      method: "POST",
      body: JSON.stringify({ doc_id: docId, page_ranges: pageRanges, split_all: splitAll }),
    }),

  compress: (docId: string, level: 1 | 2 | 3 = 2) =>
    apiFetch<Operation>("/api/compress/", {
      method: "POST",
      body: JSON.stringify({ doc_id: docId, level }),
    }),

  watermark: (docId: string, text: string, opacity = 0.3, rotation = 45) =>
    apiFetch<Operation>("/api/watermark/", {
      method: "POST",
      body: JSON.stringify({ doc_id: docId, text, opacity, rotation }),
    }),

  ocr: (docId: string, language = "spa+eng") =>
    apiFetch<Operation>("/api/ocr/", {
      method: "POST",
      body: JSON.stringify({ doc_id: docId, language }),
    }),

  rotate: (docId: string, rotations: Record<string, number> | null, rotateAll?: number) =>
    apiFetch<Operation>("/api/rotate/", {
      method: "POST",
      body: JSON.stringify({ doc_id: docId, rotations, rotate_all: rotateAll }),
    }),

  reorder: (docId: string, newOrder: number[]) =>
    apiFetch<Operation>("/api/reorder/", {
      method: "POST",
      body: JSON.stringify({ doc_id: docId, new_order: newOrder }),
    }),

  // Previews
  previews: {
    listUrl: (docId: string) => `/api/preview/${docId}/pages`,
    pageUrl: (docId: string, page: number) =>
      `${API_BASE}/api/preview/${docId}/page/${page}`,
  },

  // Descarga de outputs
  downloadOperation: (type: string, opId: string) =>
    `${API_BASE}/api/${type}/${opId}/download`,

  // Audit
  audit: (limit = 100) =>
    apiFetch<{ events: AuditEvent[]; count: number }>(`/api/audit/?limit=${limit}`),

  // Backup
  backupUrl: () => `${API_BASE}/api/backup/download`,
  backupStats: () => apiFetch<Record<string, number | string>>("/api/backup/stats"),

  // Health
  health: () => apiFetch<{ status: string }>("/health"),
};
