---
name: cidf
description: >-
  Content Insertion Decision Framework (CIDF) v1.2 — enforces the ultrathink principle
  "Use the simplest tool that works." Decides the optimal content insertion method
  (form input → typing → paste → upload → scripting), lints decisions against 5 policy
  rules, executes with automatic fallback, and verifies programmatically. Load when
  performing any content insertion into documents, web forms, or editor fields.
license: Apache-2.0
metadata:
  author: diazMelgarejo
  version: '1.2'
---

# Content Insertion Decision Framework (CIDF)

Runnable Python + TypeScript decision engine that prevents over-engineering content insertion tasks.

**Core principle:** Use the simplest tool that works. Complexity is a cost, not a feature.

## When to Use This Skill

- Inserting text, data, or files into a target field, editor, or document
- Choosing between form input, typing, clipboard paste, file upload, or scripting
- Validating that an agent's insertion plan isn't over-engineered
- Building or reviewing automation workflows that involve content placement

## Repository

All source code, specs, and tests live under:

[`ultrathink-system/single_agent/cidf/`](https://github.com/diazMelgarejo/ultrathink-system/tree/main/single_agent/cidf)

## Key Files

| File | Purpose |
|------|---------|
| [`FRAMEWORK.md`](https://github.com/diazMelgarejo/ultrathink-system/blob/main/single_agent/cidf/FRAMEWORK.md) | Full specification — the one rule, task classification, method priority order, automation gate, verification protocol, anti-patterns, and per-platform skill sets |
| [`DESIGN.md`](https://github.com/diazMelgarejo/ultrathink-system/blob/main/single_agent/cidf/DESIGN.md) | Original design document — JSON decision tree, flowcharts, decision matrices, and the meta-lesson from the Amplifier Principle |
| [`README.md`](https://github.com/diazMelgarejo/ultrathink-system/blob/main/single_agent/cidf/README.md) | Package overview, quick-start usage (Python), lint rules, how to run conformance tests |
| [`core/content_insertion_framework.py`](https://github.com/diazMelgarejo/ultrathink-system/blob/main/single_agent/cidf/core/content_insertion_framework.py) | Python decision engine — `Task`, `Env`, `Decision` dataclasses, `decide()`, `execute_with_fallback()`, `verify()` |
| [`core/contentInsertionFramework.ts`](https://github.com/diazMelgarejo/ultrathink-system/blob/main/single_agent/cidf/core/contentInsertionFramework.ts) | TypeScript mirror of the Python core — identical interfaces and logic |
| [`core/content_insertion_policy.json`](https://github.com/diazMelgarejo/ultrathink-system/blob/main/single_agent/cidf/core/content_insertion_policy.json) | Machine-parseable policy — inputs schema, tool priority with eligibility conditions, automation gate rules, lint definitions, and 6 test vectors |
| [`linter/policy_linter.py`](https://github.com/diazMelgarejo/ultrathink-system/blob/main/single_agent/cidf/linter/policy_linter.py) | Python linter enforcing LINT-001 through LINT-005 |
| [`linter/policyLinter.ts`](https://github.com/diazMelgarejo/ultrathink-system/blob/main/single_agent/cidf/linter/policyLinter.ts) | TypeScript port of the linter |
| [`tests/test_conformance.py`](https://github.com/diazMelgarejo/ultrathink-system/blob/main/single_agent/cidf/tests/test_conformance.py) | Python conformance suite (6 test vectors, run with `pytest`) |
| [`tests/conformance.test.ts`](https://github.com/diazMelgarejo/ultrathink-system/blob/main/single_agent/cidf/tests/conformance.test.ts) | TypeScript conformance suite (same 6 vectors, run with `npx jest`) |

## Method Priority Order

Always iterate top-to-bottom. Stop at the first eligible method.

| Rank | Method | Complexity | Key Gate |
|------|--------|------------|----------|
| 1 | `direct_form_input` | 1 | Field accessible, content under 10k chars |
| 2 | `direct_typing` | 2 | Editor visible, content under 5k chars |
| 3 | `clipboard_paste` | 2 | Paste supported |
| 4 | `file_upload` | 3 | Upload endpoint available |
| 5 | `scripting` | 5 | Automation gate must be OPEN |

## Automation Gate

Scripting is only eligible when the gate is open:

**OPEN** (any one true): frequency >= 5, requires conditional logic, requires transformation, requires external integration.

**CLOSED** (any one true): one-time AND static content, OR any rank 1-4 method is eligible.

When closed and all ranks 1-4 fail: notify the user — do not script.

## Lint Rules

| Rule | Fires When | Meaning |
|------|------------|---------|
| `LINT-001` | Scripting chosen while rank 1-4 eligible | Simpler method available; scripting blocked |
| `LINT-002` | `verification_required` missing or false | Verification is mandatory; cannot be disabled |
| `LINT-003` | Chosen tool complexity > minimum eligible | Complexity bias detected; use lower-rank tool |
| `LINT-004` | Scripting chosen for one-time static task | Scripting gate closed: one-time static content |
| `LINT-005` | Fallback chain empty when failure likely | No fallback defined; add at least one fallback |

## Verification Protocol

Visual confirmation is insufficient. Always verify programmatically:

1. Execute chosen method
2. Wait for UI response
3. If no visual change, refresh page once
4. Extract text programmatically (DOM query / API fetch)
5. Check that `task.signature` is present in extracted text
6. If present: log success
7. If absent: try next method in fallback chain
8. If chain exhausted: notify user with full failure log

## Quick Usage

```python
from cidf.core.content_insertion_framework import Task, Env, decide, execute_with_fallback
from cidf.linter.policy_linter import lint_strict

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
    signature="my_unique_marker",
)

env = Env(
    field_accessible=True,
    editor_visible=True,
    paste_supported=True,
    upload_available=False,
)

decision = decide(task, env)          # returns Decision with chosen_tool + fallback_chain
lint_strict(decision, task, env)      # raises LintError on any violation
result = execute_with_fallback(...)   # runs with automatic fallback + verification
```
