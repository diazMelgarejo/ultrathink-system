# Content Insertion Decision Framework
**Version:** 1.2 | **License:** Apache 2.0 | **Updated:** 2026-03-20
**Purpose:** Prevent over-engineering content insertion. Enforces simplicity-first across all AI agent frameworks.

---

## MACHINE-PARSEABLE BLOCK
<!-- agents: parse section between triple-backtick json tags -->

```json
{
  "id": "content_insertion_framework",
  "version": "1.2",
  "core_principle": "Use the simplest tool that works. Complexity is a cost, not a feature.",

  "method_registry": [
    { "rank": 1, "id": "form_input",    "complexity": 1, "requires": ["field_accessible", "content_under_10k"] },
    { "rank": 2, "id": "direct_typing", "complexity": 2, "requires": ["editor_visible",   "content_under_5k"]  },
    { "rank": 3, "id": "clipboard_paste","complexity": 2, "requires": ["paste_supported",  "formatting_ok"]     },
    { "rank": 4, "id": "file_upload",   "complexity": 3, "requires": ["upload_available",  "format_supported"]  },
    { "rank": 5, "id": "scripting",     "complexity": 5, "requires": ["automation_justified"]                   }
  ],

  "automation_gate": {
    "justified_if_any": [
      "task_frequency > 5",
      "conditional_logic_required",
      "data_transformation_needed",
      "external_system_integration"
    ],
    "blocked_if_any": [
      "one_time_operation",
      "static_content_only",
      "simpler_tool_available",
      "setup_time > execution_time"
    ]
  },

  "execution_sequence": [
    "classify_task",
    "select_lowest_rank_viable_method",
    "execute_method",
    "check_visual_confirmation",
    "if_no_visual_then_refresh",
    "verify_with_read_page",
    "if_verified_mark_complete",
    "if_failed_try_next_rank",
    "if_all_failed_notify_user"
  ],

  "verification_protocol": {
    "steps": ["execute", "check_visual", "refresh_if_needed", "read_page_programmatic", "confirm_or_escalate"],
    "rule": "Visual confirmation is insufficient. Always verify programmatically."
  },

  "anti_patterns": [
    { "id": "premature_optimization", "trigger": "scripting before trying rank 1-4",       "fix": "Always start at rank 1" },
    { "id": "visual_assumption",      "trigger": "marking complete on visual alone",        "fix": "Use read_page to verify" },
    { "id": "complexity_bias",        "trigger": "choosing complex tools as more reliable", "fix": "Enforce simplicity_first" },
    { "id": "failure_escalation",     "trigger": "pivoting to scripting on first failure",  "fix": "Exhaust all lower ranks first" }
  ],

  "integrations": {
    "langchain":  "Tool(name='InsertContent', func=insert_content_decision)",
    "crewai":     "Load framework JSON; agent calls decision_tree.evaluate(task)",
    "langgraph":  "Node reads method_registry; traverses execution_sequence as graph edges",
    "autogpt":    "YAML task with priority_check: simplicity_first, methods ranked 1-5",
    "any_agent":  "Load JSON block; iterate method_registry by rank; apply automation_gate"
  }
}
```

---

## HUMAN-READABLE SECTION

### The One Rule
> **Try the simplest tool first. Only add complexity when every simpler option has failed or automation clearly pays off.**

---

### Method Priority (Always in This Order)

| Rank | Method | Use When | Complexity |
|------|--------|----------|-----------|
| 1 | `form_input` | Field is accessible, content < 10k chars | ★☆☆☆☆ |
| 2 | `direct_typing` | Editor is visible, content < 5k chars | ★★☆☆☆ |
| 3 | `clipboard_paste` | Paste is supported and preserves formatting | ★★☆☆☆ |
| 4 | `file_upload` | Upload endpoint exists, format supported | ★★★☆☆ |
| 5 | `scripting` | **Only** when all above fail OR automation is justified | ★★★★★ |

---

### Automation Gate

Before writing any script, check both columns. **One BLOCKED item vetoes scripting.**

| ✅ Justified If (any true) | ⛔ Blocked If (any true) |
|---------------------------|------------------------|
| Task repeats 5+ times | One-time operation |
| Conditional logic required | Static content only |
| Data transformation needed | Simpler tool available |
| External system integration | Setup time > execution time |

---

### Execution Flow

```
START
  │
  ▼
Classify: one-time or repeatable?
  │
  ├─ one-time ──────────────────────────────────────────────┐
  │                                                          ▼
  │                                              Try Rank 1: form_input
  │                                                → fail → Rank 2: typing
  │                                                → fail → Rank 3: paste
  │                                                → fail → Rank 4: upload
  │                                                → fail → Apply Automation Gate
  │                                                          ├─ justified → Rank 5: script
  │                                                          └─ blocked   → notify user
  │
  └─ repeatable → Apply Automation Gate
                    ├─ justified → Rank 5: script
                    └─ blocked   → treat as one-time

After any method executes:
  1. Check visual confirmation
  2. If no visual → refresh page
  3. Verify programmatically (read_page / get_page_text)
  4. Content found? → ✅ DONE
  5. Content missing? → try next rank
  6. All ranks exhausted? → notify user
```

---

### Verification Protocol

**Never trust visual alone.** Pages lag, caches mislead, async renders deceive.

```
execute_method()
    ↓
visual_ok?  ──no──→  refresh_page()
    ↓                      ↓
    └──────────────→ read_page() / get_page_text()
                           ↓
               content_in_page?
                  yes → mark_complete()
                  no  → log_failure(); try_next_rank()
```

---

### Quick Reference Card

```
┌──────────────────────────────────────────────────────────┐
│            CONTENT INSERTION — DECISION CARD             │
│                                                          │
│  ALWAYS START AT RANK 1:                                 │
│  1 → form_input                                          │
│  2 → direct_typing                                       │
│  3 → clipboard_paste                                     │
│  4 → file_upload                                         │
│  5 → scripting  (ONLY if gate passes)                    │
│                                                          │
│  SCRIPTING RED FLAGS:                                     │
│  ⛔ One-time task                                        │
│  ⛔ Static content                                       │
│  ⛔ Simpler tool available                               │
│  ⛔ Setup time > run time                                │
│                                                          │
│  SCRIPTING GREEN LIGHTS:                                  │
│  ✅ Runs 5+ times                                        │
│  ✅ Logic or transformation required                     │
│  ✅ External system integration                          │
│                                                          │
│  VERIFY — always programmatic, never visual-only         │
└──────────────────────────────────────────────────────────┘
```

---

### Pseudo-Code (Platform-Agnostic)

```python
def insert_content(task):
    methods = [form_input, direct_typing, clipboard_paste, file_upload]

    # Automation gate: only unlock scripting if justified
    if automation_justified(task):
        methods.append(scripting)

    for method in methods:
        if requirements_met(method, task):
            execute(method, task.content)
            if not visual_updated():
                refresh_page()
            if verify_with_read_page(task.content):
                return success(method)
            log_failure(method)

    return notify_user("All methods exhausted")


def automation_justified(task):
    blocked = (task.is_one_time or task.is_static
               or simpler_tool_available() or setup_time() > run_time())
    if blocked:
        return False
    return (task.frequency > 5 or task.requires_logic
            or task.needs_transformation or task.uses_external_api)


def verify_with_read_page(content):
    return content in read_page_tool()   # programmatic, not visual
```

---

### Memory Anchors (5 Principles)

1. **Occam's Razor for Tools** — The simplest tool that works is the correct tool.
2. **Complexity Is a Cost** — Every added layer multiplies failure points.
3. **Visual ≠ Actual** — Always verify programmatically, never by appearance.
4. **Automation Has Overhead** — Justify it with frequency or logic requirements.
5. **Fail Fast, Fallback Faster** — Debug simple failures; don't escalate to complex solutions prematurely.

---

### Framework Properties

| Property | Status |
|----------|--------|
| JSON-serializable | ✅ Machine-parseable by any agent |
| Language-agnostic | ✅ Pseudo-code + flowchart, no framework lock-in |
| Platform-independent | ✅ Web, desktop, mobile, API |
| Versioned | ✅ `version` field in JSON block |
| LangChain compatible | ✅ Tool wrapper pattern |
| LangGraph compatible | ✅ Node/edge traversal pattern |
| CrewAI compatible | ✅ Agent.execute_task pattern |
| AutoGPT compatible | ✅ YAML task decomposition |

---

## Runnable Implementation: `cidf/` Package

This document is the **human-readable reference** for CIDF v1.2.
The **executable source of truth** lives in the `cidf/` package alongside this file:

```
bin/skills/
├── references/
│   └── content-insertion-framework.md   ← you are here (human reference)
└── cidf/                                 ← runnable implementation
    ├── FRAMEWORK.md                      ← canonical v1.2 specification
    ├── core/
    │   ├── content_insertion_framework.py   ← Python: decide(), verify(), execute_with_fallback()
    │   ├── content_insertion_policy.json    ← machine-parseable policy + 6 test vectors
    │   └── contentInsertionFramework.ts     ← TypeScript port
    ├── linter/
    │   ├── policy_linter.py                 ← LINT-001–005 CI guard
    │   └── policyLinter.ts
    └── tests/
        ├── test_conformance.py              ← 30 pytest tests (all must pass)
        └── conformance.test.ts
```

### Canonical Version Alignment

| Artifact | Version |
|----------|---------|
| This document (`content-insertion-framework.md`) | **1.2** |
| `cidf/FRAMEWORK.md` | **1.2** |
| `cidf/core/content_insertion_policy.json` → `framework_version` | **1.2** |
| `cidf/linter/policy_linter.py` | **1.2** |
| `cidf/tests/test_conformance.py` | asserts `framework_version == "1.2"` |

**If you update the policy**, change all five locations above in the same commit.

### Quick Import (Python)

```python
from cidf.core.content_insertion_framework import Task, Env, decide, execute_with_fallback
from cidf.linter.policy_linter import lint_strict

task = Task(is_one_time=True, frequency_estimate=1, content_static=True,
            requires_transformation=False, requires_conditional_logic=False,
            requires_external_integration=False, content_length_chars=2000,
            format_requirements="plain", signature="my_marker", task_type="content_insertion")
env  = Env(field_accessible=True, editor_visible=True, paste_supported=True, upload_available=False)

decision = decide(task, env)          # → chosen_tool: "direct_form_input"
lint_strict(decision, task, env)       # raises LintError if any of LINT-001–005 violated
```

### Run Conformance Tests

```bash
# From repo root — must all pass before any policy change ships
pytest bin/skills/cidf/tests/test_conformance.py -v   # 30 tests
```
