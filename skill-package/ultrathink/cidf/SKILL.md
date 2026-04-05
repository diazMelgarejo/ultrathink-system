---
name: cidf
description: >-
  Content Insertion Decision Framework (CIDF) v1.2 — enforces the ultrathink principle
  "Use the simplest tool that works." Decides the optimal content insertion method
  (form input → typing → paste → upload → scripting), lints decisions against 5 policy
  rules, executes with automatic fallback, and verifies programmatically. Load when
  performing any content insertion into documents, web forms, or editor fields.
version: '1.2'
license: Apache-2.0
parent_skill: ../SKILL.md
compatibility: claude-code, claude-desktop, cowork, ecc-tools, perplexity-tools
allowed-tools: bash, file-operations, web-search
sub_skills:
  - path: ../references/amplifier-principle.md
    trigger: "Need foundational philosophy on why developers must stay in the driver's seat with AI tools"
  - path: ../references/content-insertion-framework.md
    trigger: "Need machine-parseable policy JSON block and human reference for content insertion"
---

# CIDF — Content Insertion Decision Framework

Runnable Python + TypeScript decision engine that prevents over-engineering content insertion tasks.

## Recursive Loading Protocol

This SKILL.md is a **sub-skill** of [`single_agent/SKILL.md`](https://github.com/diazMelgarejo/ultrathink-system/blob/main/single_agent/SKILL.md) (the parent ultrathink skill). It provides focused context for all content insertion decisions.

**Loading behavior:**
- Agents **SHOULD** load this file when any content insertion task is detected
- Agents **CAN** recursively load deeper documents listed in `sub_skills` frontmatter when they need more detail
- Loading order: parent `SKILL.md` → this `cidf/SKILL.md` → specific sub_skill on demand

**Decision table — what to load:**

| Need | Load |
|------|------|
| Quick insertion decision | This file only (method priority + lint rules below) |
| Full specification or edge cases | `FRAMEWORK.md` |
| Design rationale, flowcharts, pseudo-code | `DESIGN.md` |
| Foundational philosophy (why humans lead) | `../references/amplifier-principle.md` |
| Machine-parseable policy for agent frameworks | `core/content_insertion_policy.json` |
| Python/TS implementation details | `core/content_insertion_framework.py` or `.ts` |

## Relationship to AFRP

AFRP (Audience-First Response Protocol) runs **before** CIDF in the processing chain. AFRP determines *what* content should exist and *for whom*. CIDF determines *how* to insert that content. When AFRP has resolved audience and abstraction level, that context should inform CIDF execution — the insertion method may vary based on who the content is for.

Loading order: `afrp/SKILL.md` → parent `SKILL.md` Router → this `cidf/SKILL.md` → specific sub_skill on demand.

## The One Rule

> Use the simplest tool that works. Complexity is a cost, not a feature.

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

## Package Map

```
cidf/
├── SKILL.md                              ← you are here (discovery + recursive loading)
├── FRAMEWORK.md                          ← full v1.2 specification
├── DESIGN.md                             ← original design doc + meta-lesson
├── README.md                             ← quick-start guide
├── core/
│   ├── content_insertion_framework.py    ← Python: decide(), verify(), execute_with_fallback()
│   ├── contentInsertionFramework.ts      ← TypeScript mirror
│   └── content_insertion_policy.json     ← machine-parseable policy + 6 test vectors
├── linter/
│   ├── policy_linter.py                  ← LINT-001–005 enforcement
│   └── policyLinter.ts                   ← TypeScript linter
└── tests/
    ├── test_conformance.py               ← pytest conformance (6 vectors)
    └── conformance.test.ts               ← jest conformance
```

## Boundaries

### Always Do
- Run `decide()` before any content insertion
- Verify programmatically after every insertion
- Start at rank 1 every time

### Ask First
- Switching from automation to manual approach
- Modifying `content_insertion_policy.json`

### Never Do
- Skip verification (LINT-002)
- Jump directly to scripting without trying ranks 1-4
- Trust visual confirmation alone
- Mark complete without programmatic verification
