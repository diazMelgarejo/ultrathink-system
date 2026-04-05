/**
 * tests/conformance.test.ts
 * ──────────────────────────
 * Conformance test suite for Content Insertion Decision Framework v1.2.
 * Same 6 test vectors as the Python suite. Results must be identical.
 *
 * Run:
 *   npx jest tests/conformance.test.ts
 *   or: npx ts-jest tests/conformance.test.ts
 */

import {
  Task, Env, Decision, ToolName,
  decide, automationJustified, verify, executeWithFallback,
  Verifier,
} from "../core/contentInsertionFramework";

import { lint, LintViolation } from "../linter/policyLinter";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    task_type:                    "content_insertion",
    is_one_time:                  true,
    frequency_estimate:           1,
    content_static:               true,
    requires_transformation:      false,
    requires_conditional_logic:   false,
    requires_external_integration:false,
    content_length_chars:         1_200,
    format_requirements:          "plain",
    signature:                    "test_signature_abc",
    ...overrides,
  };
}

function makeEnv(overrides: Partial<Env> = {}): Env {
  return {
    field_accessible:           true,
    editor_visible:             true,
    paste_supported:            true,
    upload_available:           false,
    max_safe_chars_form_input:  10_000,
    max_safe_chars_typing:      5_000,
    formatting_preserved_on_paste: true,
    ...overrides,
  };
}

class FakeVerifier implements Verifier {
  refreshCalled = false;
  constructor(private contentStore: string = "") {}

  async refreshOnceIfNeeded(): Promise<void> {
    this.refreshCalled = true;
  }

  async extractText(): Promise<string> {
    return this.contentStore;
  }
}

// ─── TV-01: Static text, field accessible ─────────────────────────────────────

describe("TV-01: Static text 2k chars, field accessible", () => {
  const task     = makeTask({ content_length_chars: 2_000 });
  const env      = makeEnv({ field_accessible: true, editor_visible: true, paste_supported: true });
  const decision = decide(task, env);

  test("chosen_tool is direct_form_input", () => {
    expect(decision.chosen_tool).toBe("direct_form_input");
  });

  test("automation is not justified", () => {
    expect(decision.automation_justified).toBe(false);
    expect(automationJustified(task)).toBe(false);
  });

  test("has at least one fallback", () => {
    expect(decision.fallback_chain.length).toBeGreaterThan(0);
  });

  test("verification_required is true", () => {
    expect(decision.verification_required).toBe(true);
  });

  test("no lint errors", () => {
    const errors = lint(decision, task, env).filter(v => v.severity === "error");
    expect(errors).toHaveLength(0);
  });
});

// ─── TV-02: Static text 12k chars, field over limit ───────────────────────────

describe("TV-02: 12k chars, field over limit", () => {
  const task     = makeTask({ content_length_chars: 12_000 });
  const env      = makeEnv({ field_accessible: true, editor_visible: false,
                             paste_supported: true, upload_available: true });
  const decision = decide(task, env);

  test("chosen_tool is clipboard_paste", () => {
    expect(decision.chosen_tool).toBe("clipboard_paste");
  });

  test("direct_form_input not chosen (over limit)", () => {
    expect(decision.chosen_tool).not.toBe("direct_form_input");
  });

  test("scripting not chosen", () => {
    expect(decision.chosen_tool).not.toBe("scripting");
  });

  test("no lint errors", () => {
    const errors = lint(decision, task, env).filter(v => v.severity === "error");
    expect(errors).toHaveLength(0);
  });
});

// ─── TV-03: Rich text, editor visible ────────────────────────────────────────

describe("TV-03: Rich text, editor visible + paste available", () => {
  const task     = makeTask({ content_length_chars: 3_000, format_requirements: "rich_text" });
  const env      = makeEnv({ field_accessible: false, editor_visible: true,
                             paste_supported: true, upload_available: false });
  const decision = decide(task, env);

  test("chosen_tool is direct_typing (rank 2 over rank 3)", () => {
    expect(decision.chosen_tool).toBe("direct_typing");
  });

  test("clipboard_paste is in fallback", () => {
    expect(decision.fallback_chain).toContain("clipboard_paste");
  });

  test("no lint errors", () => {
    const errors = lint(decision, task, env).filter(v => v.severity === "error");
    expect(errors).toHaveLength(0);
  });
});

// ─── TV-04: No simple methods, upload available ───────────────────────────────

describe("TV-04: All blocked except upload", () => {
  const task     = makeTask({ content_length_chars: 4_000 });
  const env      = makeEnv({ field_accessible: false, editor_visible: false,
                             paste_supported: false, upload_available: true });
  const decision = decide(task, env);

  test("chosen_tool is file_upload", () => {
    expect(decision.chosen_tool).toBe("file_upload");
  });

  test("scripting not chosen", () => {
    expect(decision.chosen_tool).not.toBe("scripting");
  });

  test("no lint errors", () => {
    const errors = lint(decision, task, env).filter(v => v.severity === "error");
    expect(errors).toHaveLength(0);
  });
});

// ─── TV-05: Repeatable + logic, but field accessible ─────────────────────────

describe("TV-05: Repeatable template, conditional logic, field accessible", () => {
  const task = makeTask({
    is_one_time: false,
    frequency_estimate: 20,
    content_static: false,
    requires_conditional_logic: true,
    content_length_chars: 500,
  });
  const env      = makeEnv({ field_accessible: true, editor_visible: true,
                             paste_supported: true, upload_available: true });
  const decision = decide(task, env);

  test("automation_justified is true", () => {
    expect(decision.automation_justified).toBe(true);
    expect(automationJustified(task)).toBe(true);
  });

  test("chosen_tool is still direct_form_input (simplicity-first)", () => {
    expect(decision.chosen_tool).toBe("direct_form_input");
  });

  test("scripting is in fallback chain", () => {
    expect(decision.fallback_chain).toContain("scripting");
  });

  test("no lint errors", () => {
    const errors = lint(decision, task, env).filter(v => v.severity === "error");
    expect(errors).toHaveLength(0);
  });
});

// ─── TV-06: UI lag — verify without duplicate insert ─────────────────────────

describe("TV-06: UI lag — refresh then verify, no duplicate insert", () => {
  const task     = makeTask({ content_length_chars: 500, signature: "hello_world_marker" });
  const env      = makeEnv({ field_accessible: true });
  const decision = decide(task, env);

  test("chosen_tool is direct_form_input", () => {
    expect(decision.chosen_tool).toBe("direct_form_input");
  });

  test("verify finds content after lag", async () => {
    const verifier = new FakeVerifier("some text hello_world_marker more text");
    const result = await verify(verifier, "hello_world_marker");
    expect(result).toBe(true);
    expect(verifier.refreshCalled).toBe(true);
  });

  test("verify fails cleanly when absent", async () => {
    const verifier = new FakeVerifier("unrelated content");
    const result = await verify(verifier, "hello_world_marker");
    expect(result).toBe(false);
  });

  test("execution does not duplicate on lag", async () => {
    let insertCallCount = 0;
    const verifier = new FakeVerifier("pre-existing hello_world_marker");

    const result = await executeWithFallback(
      decision,
      { direct_form_input: async (_: string) => { insertCallCount++; } },
      verifier,
      "test content",
      "hello_world_marker",
    );

    expect(result.status).toBe("success");
    expect(result.tool).toBe("direct_form_input");
    expect(insertCallCount).toBe(1);  // must not insert twice
  });
});

// ─── Linter conformance ───────────────────────────────────────────────────────

describe("Linter: catches all five anti-patterns", () => {

  test("LINT-001: scripting while simpler eligible", () => {
    const task = makeTask();
    const env  = makeEnv({ field_accessible: true });
    const bad: Decision = {
      chosen_tool: "scripting",
      fallback_chain: [],
      reason_codes: ["forced"],
      automation_justified: true,
      verification_required: true,
    };
    const ids = lint(bad, task, env).map(v => v.rule_id);
    expect(ids).toContain("LINT-001");
    expect(ids).toContain("LINT-003");
  });

  test("LINT-002: verification disabled", () => {
    const task     = makeTask();
    const env      = makeEnv();
    const decision = decide(task, env);
    (decision as any).verification_required = false;
    const ids = lint(decision, task, env).map(v => v.rule_id);
    expect(ids).toContain("LINT-002");
  });

  test("LINT-004: scripting for one-time static task", () => {
    const task = makeTask({ is_one_time: true, content_static: true, frequency_estimate: 1 });
    const env  = makeEnv({ field_accessible: false, editor_visible: false,
                           paste_supported: false, upload_available: false });
    const bad: Decision = {
      chosen_tool: "scripting",
      fallback_chain: [],
      reason_codes: ["forced"],
      automation_justified: false,
      verification_required: true,
    };
    const ids = lint(bad, task, env).map(v => v.rule_id);
    expect(ids).toContain("LINT-004");
  });

  test("LINT-005: no fallback defined (warning)", () => {
    const task     = makeTask();
    const env      = makeEnv({ field_accessible: true, editor_visible: false,
                               paste_supported: false, upload_available: false });
    const decision = decide(task, env);
    decision.fallback_chain = [];
    const warnings = lint(decision, task, env).filter(v => v.severity === "warning");
    expect(warnings.some(v => v.rule_id === "LINT-005")).toBe(true);
  });

  test("clean decision passes all rules", () => {
    const task     = makeTask();
    const env      = makeEnv();
    const decision = decide(task, env);
    const errors   = lint(decision, task, env).filter(v => v.severity === "error");
    expect(errors).toHaveLength(0);
  });
});
