import { apiFetch } from "./client";

export interface Artifact {
  artifact_id?: string;
  id?: string;
  name?: string;
  kind?: string;
  size_bytes?: number;
  url?: string;
  created_at?: string;
  job_id?: string;
  [k: string]: unknown;
}

export interface ArtifactsResponse {
  available: boolean;
  source: string;
  artifacts: Artifact[];
  error?: string | null;
}

export const listJobArtifacts = (jobId: string, signal?: AbortSignal) =>
  apiFetch<ArtifactsResponse>(
    `/api/jobs/${encodeURIComponent(jobId)}/artifacts`,
    { signal },
  );
