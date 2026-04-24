/**
 * linter/policyLinter.ts
 * ───────────────────────
 * Policy linter for Content Insertion Decision Framework v1.2.
 * TypeScript port — identical lint rules to Python version.
 *
 * Usage:
 *   import { lint, lintStrict } from "./linter/policyLinter";
 *   const violations = lint(decision, task, env);
 *   if (violations.length) throw new LintError(violations);
 */

import { Decision, Task, Env, ToolName } from "../core/contentInsertionFramework";

// ─── Lint result ──────────────────────────────────────────────────────────────

export interface LintViolation {
  rule_id: string;
  message: string;
  severity: "error" | "warning";
}

export class LintError extends Error {
  constructor(public violations: LintViolation[]) {
    const lines = violations.map(v => `  [${v.rule_id}] ${v.message}`).join("\n");
    super(`Policy lint failed:\n${lines}`);
  }
}

// ─── Tool complexity map ──────────────────────────────────────────────────────

const TOOL_COMPLEXITY: Record<ToolName, number> = {
  direct_form_input: 1,
  direct_typing:     2,
  clipboard_paste:   2,
  file_upload:       3,
  scripting:         5,
};

function minEligibleComplexity(task: Task, env: Env): number {
  const maxForm   = env.max_safe_chars_form_input ?? 10_000;
  const maxTyping = env.max_safe_chars_typing ?? 5_000;
  if (env.field_accessible && task.content_length_chars <= maxForm)   return 1;
  if (env.editor_visible   && task.content_length_chars <= maxTyping) return 2;
  if (env.paste_supported)   return 2;
  if (env.upload_available)  return 3;
  return 5;
}

function anySimpleMethodEligible(task: Task, env: Env): boolean {
  return minEligibleComplexity(task, env) < 5;
}

// ─── Lint rules ───────────────────────────────────────────────────────────────

export function lint(decision: Decision, task: Task, env: Env): LintViolation[] {
  const violations: LintViolation[] = [];
  const minC = minEligibleComplexity(task, env);
  const chosenC = TOOL_COMPLEXITY[decision.chosen_tool] ?? 99;

  // LINT-001: Scripting while simpler methods are eligible
  if (decision.chosen_tool === "scripting" && anySimpleMethodEligible(task, env)) {
    violations.push({
      rule_id: "LINT-001",
      message: `Scripting chosen but simpler method eligible (min eligible complexity: ${minC}). Iterate from rank 1 first.`,
      severity: "error",
    });
  }

  // LINT-002: verification_required must always be true
  if (!decision.verification_required) {
    violations.push({
      rule_id: "LINT-002",
      message: "verification_required is false or missing. Verification is mandatory and cannot be disabled.",
      severity: "error",
    });
  }

  // LINT-003: Complexity bias
  if (chosenC > minC) {
    violations.push({
      rule_id: "LINT-003",
      message: `Complexity bias: chosen '${decision.chosen_tool}' (complexity=${chosenC}) but a simpler method is eligible (min complexity=${minC}).`,
      severity: "error",
    });
  }

  // LINT-004: Scripting for one-time static task
  if (decision.chosen_tool === "scripting" && task.is_one_time && task.content_static) {
    violations.push({
      rule_id: "LINT-004",
      message: "Scripting gate is CLOSED: task is one-time and content is static. Use the simplest eligible method instead.",
      severity: "error",
    });
  }

  // LINT-005: No fallback defined
  if (decision.fallback_chain.length === 0 && decision.chosen_tool !== "scripting") {
    violations.push({
      rule_id: "LINT-005",
      message: `No fallback_chain defined for chosen tool '${decision.chosen_tool}'. Add at least one fallback.`,
      severity: "warning",
    });
  }

  return violations;
}

export function lintStrict(decision: Decision, task: Task, env: Env): void {
  const violations = lint(decision, task, env);
  if (violations.length > 0) throw new LintError(violations);
}

export function lintErrorsOnly(decision: Decision, task: Task, env: Env): void {
  const violations = lint(decision, task, env).filter(v => v.severity === "error");
  if (violations.length > 0) throw new LintError(violations);
}
