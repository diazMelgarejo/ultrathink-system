import { apiFetch } from "./client";

/** Generic wrapper for a single backend-aggregated section. */
export interface AppStateSection<T = unknown> {
  available: boolean;
  source: string;
  data: T;
  error?: string | null;
}

export interface AppState {
  portal: AppStateSection;
  runtime: AppStateSection;
  models: AppStateSection;
  activity: AppStateSection<{ events: unknown[] }>;
  jobs: AppStateSection<{ jobs: JobSummary[] }>;
}

export interface JobSummary {
  job_id?: string;
  id?: string;
  intent?: string;
  prompt?: string;
  status?: string;
  backend?: string;
  device?: string;
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, unknown>;
}

export const fetchAppState = (signal?: AbortSignal) =>
  apiFetch<AppState>("/api/app/state", { signal });
