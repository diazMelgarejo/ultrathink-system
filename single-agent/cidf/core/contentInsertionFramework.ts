/**
 * contentInsertionFramework.ts
 * ─────────────────────────────
 * Platform-agnostic TypeScript library for Content Insertion Decision Framework v1.2.
 * All TypeScript-based integrations (OpenClaw, etc.) import from here.
 *
 * No runtime dependencies required.
 */

// ─── Types ────────────────────────────────────────────────────────────────────

export type TaskType = "content_insertion" | "automation" | "data_processing";
export type FormatRequirement = "plain" | "rich_text" | "strict_layout";
export type ToolName =
  | "direct_form_input"
  | "direct_typing"
  | "clipboard_paste"
  | "file_upload"
  | "scripting";

export interface Task {
  task_type: TaskType;
  is_one_time: boolean;
  frequency_estimate: number;
  content_static: boolean;
  requires_transformation: boolean;
  requires_conditional_logic: boolean;
  requires_external_integration: boolean;
  content_length_chars: number;
  format_requirements: FormatRequirement;
  signature: string;               // substring used to verify insertion succeeded
}

export interface Env {
  field_accessible: boolean;
  editor_visible: boolean;
  paste_supported: boolean;
  upload_available: boolean;
  max_safe_chars_form_input?: number;    // default 10000
  max_safe_chars_typing?: number;        // default 5000
  formatting_preserved_on_paste?: boolean;
}

export interface Decision {
  chosen_tool: ToolName;
  fallback_chain: ToolName[];
  reason_codes: string[];
  automation_justified: boolean;
  verification_required: true;
}

export interface Verifier {
  refreshOnceIfNeeded(): Promise<void>;
  extractText(): Promise<string>;
}

export interface AttemptLog {
  tool: ToolName;
  result: "success" | "verification_failed" | "no_executor_registered";
}

export interface ExecutionResult {
  status: "success" | "failed";
  tool?: ToolName;
  attempts: AttemptLog[];
}

// ─── Core logic ───────────────────────────────────────────────────────────────

export function automationJustified(task: Task): boolean {
  return (
    task.frequency_estimate >= 5 ||
    task.requires_conditional_logic ||
    task.requires_transformation ||
    task.requires_external_integration
  );
}

export function decide(task: Task, env: Env): Decision {
  const maxForm   = env.max_safe_chars_form_input ?? 10_000;
  const maxTyping = env.max_safe_chars_typing ?? 5_000;

  const reasons: string[] = [];
  const tools: ToolName[] = [];

  if (env.field_accessible && task.content_length_chars <= maxForm)   tools.push("direct_form_input");
  if (env.editor_visible   && task.content_length_chars <= maxTyping) tools.push("direct_typing");
  if (env.paste_supported)   tools.push("clipboard_paste");
  if (env.upload_available)  tools.push("file_upload");

  const justified = automationJustified(task);
  if (justified) tools.push("scripting");

  if (tools.length === 0) {
    tools.push(justified ? "scripting" : "direct_typing");
    reasons.push("fallback_to_default_no_env_match");
  }

  let chosen: ToolName   = tools[0];
  let fallback: ToolName[] = tools.slice(1);

  if (chosen === "scripting" && task.is_one_time && task.content_static) {
    reasons.push("blocked_scripting_one_time_static");
    chosen   = fallback[0] ?? "direct_typing";
    fallback = fallback.slice(1);
  }

  reasons.push(`chosen_${chosen}`);
  reasons.push(`automation_justified=${justified}`);

  return {
    chosen_tool: chosen,
    fallback_chain: fallback,
    reason_codes: reasons,
    automation_justified: justified,
    verification_required: true,
  };
}

// ─── Verification ─────────────────────────────────────────────────────────────

export async function verify(verifier: Verifier, signature: string): Promise<boolean> {
  await verifier.refreshOnceIfNeeded();
  const text = await verifier.extractText();
  return text.includes(signature);
}

// ─── Execution loop ───────────────────────────────────────────────────────────

export async function executeWithFallback(
  decision: Decision,
  executors: Partial<Record<ToolName, (content: string) => Promise<void>>>,
  verifier: Verifier,
  content: string,
  signature: string,
): Promise<ExecutionResult> {
  const chain: ToolName[] = [decision.chosen_tool, ...decision.fallback_chain];
  const attempts: AttemptLog[] = [];

  for (const tool of chain) {
    const executor = executors[tool];
    if (!executor) {
      attempts.push({ tool, result: "no_executor_registered" });
      continue;
    }
    await executor(content);
    const ok = await verify(verifier, signature);
    if (ok) return { status: "success", tool, attempts };
    attempts.push({ tool, result: "verification_failed" });
  }

  return { status: "failed", attempts };
}
