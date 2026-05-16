import { apiFetch } from "./client";
import type { JobSummary } from "./appState";

export interface JobsListResponse {
  available: boolean;
  source: string;
  jobs: JobSummary[];
  error?: string | null;
}

export interface JobDetail extends JobSummary {
  artifacts?: unknown[];
  events?: unknown[];
}

export const listJobs = (status?: string, signal?: AbortSignal) => {
  const qs = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<JobsListResponse>(`/api/jobs${qs}`, { signal });
};

export const getJob = (jobId: string, signal?: AbortSignal) =>
  apiFetch<JobDetail>(`/api/jobs/${encodeURIComponent(jobId)}`, { signal });

export const cancelJob = (jobId: string, signal?: AbortSignal) =>
  apiFetch<{ ok: boolean; [k: string]: unknown }>(
    `/api/jobs/${encodeURIComponent(jobId)}/cancel`,
    { method: "POST", signal },
  );

export const replayJob = (jobId: string, signal?: AbortSignal) =>
  apiFetch<{ ok: boolean; new_job_id?: string; [k: string]: unknown }>(
    `/api/jobs/${encodeURIComponent(jobId)}/replay`,
    { method: "POST", signal },
  );
