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
    job_id: "run_01JY6Z8K3M7Q",
    intent: "analysis",
    prompt: "Analyze financial report ...",
    status: "queued",
    backend: "ollama-mac",
    device: "mac",
    created_at: NOW,
  },
  {
    job_id: "run_01JY6YXR8KD9",
    intent: "analysis",
    prompt: "Threat model new API ...",
    status: "running",
    backend: "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
    device: "shared",
    created_at: NOW,
  },
  {
    job_id: "run_01JY6W7B2NS7",
    intent: "research",
    prompt: "Market research: AI agents ...",
    status: "waiting",
    backend: "openrouter/minimax/minimax-m2.5:free",
    device: "shared",
    created_at: NOW,
  },
  {
    job_id: "run_01JY6V3P9QH2",
    intent: "coding",
    prompt: "Codebase refactor plan ...",
    status: "failed",
    backend: "openrouter/minimax/minimax-m2.5:free",
    device: "shared",
    created_at: NOW,
  },
  {
    job_id: "run_01JY6U0E1LA4",
    intent: "research",
    prompt: "Customer feedback analysis ...",
    status: "succeeded",
    backend: "ollama-mac",
    device: "mac",
    created_at: NOW,
  },
  {
    job_id: "run_01JY6T6D7GZ0",
    intent: "ops",
    prompt: "Compliance checklist gen ...",
    status: "succeeded",
    backend: "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
    device: "shared",
    created_at: NOW,
  },
  {
    job_id: "run_01JY6S0H4KJ3",
    intent: "analysis",
    prompt: "Data pipeline audit ...",
    status: "failed",
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
    artifact_id: "art_01JY6YXR8KD9_01",
    name: "executive_summary.md",
    kind: "summary_md",
    size_bytes: 2_815,
    job_id: "run_01JY6YXR8KD9",
    summary: "1-page executive summary with key risks and opportunities.",
    created_at: NOW,
  },
  {
    artifact_id: "art_01JY6YXR8KD9_02",
    name: "risk_factors.csv",
    kind: "csv",
    size_bytes: 4_120,
    job_id: "run_01JY6YXR8KD9",
    summary: "Identified 12 key risk factors with likelihood and impact.",
    created_at: NOW,
  },
  {
    artifact_id: "art_01JY6YXR8KD9_03",
    name: "opportunities.md",
    kind: "notes_md",
    size_bytes: 1_840,
    job_id: "run_01JY6YXR8KD9",
    summary: "Top 6 opportunities with strategic recommendations.",
    created_at: NOW,
  },
  {
    artifact_id: "art_01JY6YXR8KD9_04",
    name: "appendix_sources.md",
    kind: "references_md",
    size_bytes: 980,
    job_id: "run_01JY6YXR8KD9",
    summary: "Source list and references.",
    created_at: NOW,
  },
];

export const mockState: AppState = {
  portal: {
    available: true,
    source: "mock:portal",
    data: {
      version: "0.9.3",
      env: "production",
      region: "us-east-1",
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
      gateway_p95: "p95 142ms",
      hw_violations: 2,
      hardware_policy: "warn",
      ollama_mac_model: "5.2.1",
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
