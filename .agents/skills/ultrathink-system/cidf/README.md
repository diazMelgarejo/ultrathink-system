# Content Insertion Decision Framework (CIDF) v1.2
**Runnable implementation package — Python + TypeScript**

The CIDF is the executable core of the ultrathink Content Insertion principle:
> *Use the simplest tool that works. Complexity is a cost, not a feature.*

---

## Package Structure

```
cidf/
├── core/
│   ├── content_insertion_framework.py    # Python decision engine
│   ├── content_insertion_policy.json     # Machine-parseable policy + 6 test vectors
│   └── contentInsertionFramework.ts      # TypeScript decision engine
├── linter/
│   ├── policy_linter.py                  # Python policy linter (LINT-001–005)
│   └── policyLinter.ts                   # TypeScript linter
├── tests/
│   ├── test_conformance.py               # pytest conformance suite (6 test vectors)
│   └── conformance.test.ts               # TypeScript conformance suite
└── FRAMEWORK.md                          # Full framework specification
```

---

## Quick Usage (Python)

```python
from cidf.core.content_insertion_framework import Task, Env, decide, execute_with_fallback
from cidf.linter.policy_linter import lint_strict

# 1. Describe the task and environment
task = Task(
    task_type="content_insertion",
    is_one_time=True,
    frequency_estimate=1,
    content_static=True,
    requires_transformation=False,
    requires_conditional_logic=False,
    requires_external_integration=False,
    content_length_chars=3000,
    format_requirements="plain",
    signature="my_unique_marker_abc",
)

env = Env(
    field_accessible=True,
    editor_visible=True,
    paste_supported=True,
    upload_available=False,
)

# 2. Get a decision (always starts from rank 1)
decision = decide(task, env)
print(decision.chosen_tool)       # → "direct_form_input"
print(decision.fallback_chain)    # → ["direct_typing", "clipboard_paste"]

# 3. Lint before executing (catches LINT-001–005)
lint_strict(decision, task, env)  # raises LintError if violated

# 4. Execute with automatic fallback + programmatic verification
result = execute_with_fallback(
    decision=decision,
    executors={"direct_form_input": lambda content: your_insert_fn(content)},
    verifier=your_verifier,
    content="Your content here",
    signature="my_unique_marker_abc",
)
print(result.status)  # "success" or "failed"
```

---

## Run the Conformance Tests

```bash
# Python (from repo root)
pytest single_agent/cidf/tests/test_conformance.py -v

# TypeScript (requires Node + jest)
cd single_agent/cidf && npx jest tests/conformance.test.ts
```

---

## The 5 Lint Rules

| Rule | What it catches |
|------|----------------|
| LINT-001 | Scripting chosen while simpler methods are eligible |
| LINT-002 | `verification_required` disabled — never allowed |
| LINT-003 | Complexity bias — tool more complex than necessary |
| LINT-004 | Scripting for a one-time static task — hard block |
| LINT-005 | No fallback chain defined (warning) |

---

## Integration with ultrathink

The CIDF is triggered during **Stage 2 (Visionary Architecture)** whenever a task
involves content or data insertion. It enforces the Content Insertion principle from
`single_agent/SKILL.md` with executable code instead of just documentation.

The `content_insertion_policy.json` is machine-parseable by LangChain, CrewAI,
LangGraph, AutoGPT, and any MCP-compatible framework.

---

*CIDF v1.2 | Apache 2.0 | Part of ultrathink-system*
