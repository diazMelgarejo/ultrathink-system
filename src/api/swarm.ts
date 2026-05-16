import { apiFetch } from "./client";

export type TaskType = "coding" | "reasoning" | "research" | "ops";
export type OptimizeFor = "speed" | "quality" | "reliability";
export type PreferredDevice = "mac" | "windows" | "shared" | "auto";

export interface SwarmPreviewRequest {
  objective: string;
  task_type?: TaskType;
  optimize_for?: OptimizeFor;
  preferred_device?: PreferredDevice;
  metadata?: Record<string, unknown>;
}

export interface SwarmLaunchRequest extends SwarmPreviewRequest {
  approved: true;
}

export interface SwarmAssignment {
  role: string;
  specialization: string;
  intent: string;
  backend_hint: string;
  expected_output_shape: string;
  verification_rubric: string;
  routing_source: string;
}

export interface HardwarePolicyResult {
  ok: boolean;
  violations: Array<{
    role?: string;
    model?: string;
    reason?: string;
    message?: string;
    [k: string]: unknown;
  }>;
}

export interface SwarmPreview {
  objective: string;
  task_type: TaskType;
  optimize_for: OptimizeFor;
  preferred_device: PreferredDevice;
  assignments: SwarmAssignment[];
  hardware_policy: HardwarePolicyResult;
  [k: string]: unknown;
}

export interface SwarmLaunchAcceptedJob {
  role: string;
  job_id?: string;
  response: unknown;
}

export interface SwarmLaunchResult {
  accepted: boolean;
  blocked: boolean;
  session_id: string;
  accepted_jobs: SwarmLaunchAcceptedJob[];
  failed_jobs: Array<{ role: string; error: string; request: unknown }>;
  preview: SwarmPreview;
}

export const previewSwarm = (req: SwarmPreviewRequest, signal?: AbortSignal) =>
  apiFetch<SwarmPreview>("/api/swarm/preview", {
    method: "POST",
    body: req,
    signal,
  });

export const launchSwarm = (req: SwarmLaunchRequest, signal?: AbortSignal) =>
  apiFetch<SwarmLaunchResult>("/api/swarm/launch", {
    method: "POST",
    body: req,
    signal,
  });
