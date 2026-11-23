const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_URL}/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json() as Promise<{ status: string }>;
}

// --- Types ---

export interface VersionMeta {
  index: number;
  row_count: number;
  column_count: number;
}

export interface StepRunMeta {
  step_id: string;
  params: Record<string, unknown>;
  input_version: number;
  output_version: number;
  ran_at: string;
}

export interface ResultTable {
  title: string;
  columns: string[];
  rows: unknown[][];
}

export interface ProfileResult {
  tables: ResultTable[];
  charts: unknown[];
  files: unknown[];
  change_log: unknown[];
  facts: Record<string, unknown>;
  warnings: string[];
}

export interface SessionState {
  id: string;
  created_at: string;
  expires_at: string;
  current_version: number | null;
  versions: VersionMeta[];
  history: StepRunMeta[];
}

export interface CreateSessionResponse extends SessionState {
  profile: ProfileResult;
}

export interface SampleMeta {
  name: string;
  filename: string;
  description: string;
}

// --- API functions ---

export async function getSamples(): Promise<{ samples: SampleMeta[] }> {
  const res = await fetch(`${API_URL}/samples`);
  if (!res.ok) throw new Error("Failed to fetch samples");
  return res.json() as Promise<{ samples: SampleMeta[] }>;
}

export async function createSessionFromFile(
  file: File
): Promise<CreateSessionResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/sessions`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    const msg =
      (err as { detail?: { error?: { message?: string } } })?.detail?.error
        ?.message ?? "Upload failed";
    const code =
      (err as { detail?: { error?: { code?: string } } })?.detail?.error
        ?.code ?? "upload_failed";
    const error = new Error(msg) as Error & { code?: string; status?: number };
    error.code = code;
    error.status = res.status;
    throw error;
  }
  return res.json() as Promise<CreateSessionResponse>;
}

export async function createSessionFromSample(
  name: string
): Promise<CreateSessionResponse> {
  const form = new FormData();
  form.append("sample_name", name);
  const res = await fetch(`${API_URL}/sessions`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    const msg =
      (err as { detail?: { error?: { message?: string } } })?.detail?.error
        ?.message ?? "Failed to load sample";
    throw new Error(msg);
  }
  return res.json() as Promise<CreateSessionResponse>;
}

export async function getSession(id: string): Promise<SessionState> {
  const res = await fetch(`${API_URL}/sessions/${id}`);
  if (!res.ok) throw new Error("Session not found");
  return res.json() as Promise<SessionState>;
}
