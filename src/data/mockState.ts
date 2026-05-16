/**
 * Mock state seed — fallback / dev fixture matching backend shapes.
 * Used by the operator console when /api/app/state is unavailable
 * or during initial render before the first fetch resolves.
 *
 * Source of truth for SHAPES is src/api/* — keep this file in sync if
 * those types evolve.
 */
import type { AppState, JobSummary } from "@/api/appState";
import type { SwarmAssignment, SwarmPreview } from "@/api/swarm";
import type { Artifact } from "@/api/artifacts";

const NOW = new Date().toISOString();

const mockJobs: JobSummary[] = [
  {
    job_id: "job_001",
    intent: "code-review",
    prompt: "Review portal_server.py for risky patterns",
    status: "completed",
    backend: "ollama-mac",
    device: "mac",
    created_at: NOW,
  },
  {
    job_id: "job_002",
    intent: "research",
    prompt: "Audit MCP_ORCHESTRATION docs for drift",
    status: "running",
    backend: "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
    device: "shared",
    created_at: NOW,
  },
  {
    job_id: "job_003",
    intent: "verifier",
    prompt: "Verify hardware policy invariants",
    status: "queued",
    backend: "ollama-mac",
    device: "mac",
    created_at: NOW,
  },
];

const mockAssignments: SwarmAssignment[] = [
  {
    role: "context-builder",
    specialization: "research",
    intent: "summarize_context",
    backend_hint: "ollama-mac",
    expected_output_shape: "context_summary_v1",
    verification_rubric: "completeness>0.8",
    routing_source: "policy.research.mac",
  },
  {
    role: "executor",
    specialization: "coding",
    intent: "generate_solution",
    backend_hint: "openrouter/minimax/minimax-m2.5:free",
    expected_output_shape: "solution_diff_v1",
    verification_rubric: "tests_pass=true",
    routing_source: "policy.coding.openrouter",
  },
  {
    role: "verifier",
    specialization: "verification",
    intent: "verify_solution",
    backend_hint: "ollama-mac",
    expected_output_shape: "verifier_verdict_v1",
    verification_rubric: "verdict in [approved,rejected]",
    routing_source: "policy.verification.local",
  },
  {
    role: "crystallizer",
    specialization: "synthesis",
    intent: "crystallize_outcome",
    backend_hint: "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
    expected_output_shape: "crystal_summary_v1",
    verification_rubric: "verifier_approved=true",
    routing_source: "policy.synthesis.openrouter",
  },
  {
    role: "reporter",
    specialization: "documentation",
    intent: "write_report",
    backend_hint: "openrouter/minimax/minimax-m2.5:free",
    expected_output_shape: "markdown_report_v1",
    verification_rubric: "length>500",
    routing_source: "policy.reporting.openrouter",
  },
];

const mockPreview: SwarmPreview = {
  objective: "Ship orama-system v1.0.0.0 RC-1",
  task_type: "ops",
  optimize_for: "quality",
  preferred_device: "auto",
  assignments: mockAssignments,
  hardware_policy: {
    ok: true,
    violations: [],
  },
};

const mockArtifacts: Artifact[] = [
  {
    artifact_id: "art_001",
    name: "swarm-preview.json",
    kind: "preview_snapshot",
    size_bytes: 2_815,
    job_id: "job_001",
    created_at: NOW,
  },
  {
    artifact_id: "art_002",
    name: "verifier-verdict.json",
    kind: "verifier_result",
    size_bytes: 412,
    job_id: "job_001",
    created_at: NOW,
  },
];

export const mockState: AppState = {
  portal: {
    available: true,
    source: "mock:portal",
    data: {
      version: "0.9.9.8",
      env: "dev",
      region: "lan",
      stage: "RC-1",
    },
  },
  runtime: {
    available: true,
    source: "mock:pt-runtime",
    data: {
      ollama_mac: "online",
      lmstudio_win: "online",
      openrouter: "online",
    },
  },
  models: {
    available: true,
    source: "mock:pt-models",
    data: {
      mac_primary: "ollama/qwen3.5:9b-nvfp4",
      win_primary: "lmstudio-win/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2",
      openrouter_primary: "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
    },
  },
  activity: {
    available: true,
    source: "mock:pt-activity",
    data: { events: [] },
  },
  jobs: {
    available: true,
    source: "mock:pt-jobs",
    data: { jobs: mockJobs },
  },
};

export const mockSwarmPreview = mockPreview;
export const mockArtifactList = mockArtifacts;
