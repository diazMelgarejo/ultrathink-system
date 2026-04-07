---
name: cidf
description: Content Insertion Decision Framework v1.2 — sub-skill. Provides the executable decide(), lint_strict(), and execute_with_fallback() API for content insertion decisions. Activates whenever content must be inserted, written, pasted, uploaded, or scripted.
version: 1.2.0
license: Apache 2.0
compatibility: claude-code, cowork, open, codex, clawdbot
allowed-tools: bash, file-operations
---

# CIDF Sub-Skill — Content Insertion Decision Framework v1.2

**Sub-skill of `bin/skills/SKILL.md`. Load on demand for any content insertion task.**

---

## The One Rule
> Use the simplest tool that works. Complexity is a cost, not a feature.

---

## Quick API

```python
from bin.skills.cidf.core.content_insertion_framework import Task, Env, decide
from bin.skills.cidf.linter.policy_linter import lint_strict

decision = decide(task, env)      # always starts at rank 1
lint_strict(decision, task, env)  # raises LintError on LINT-001–005
```

---

## Method Priority (always top-to-bottom, stop at first eligible)

| Rank | Method | Eligible When | Complexity |
|------|--------|---------------|-----------|
| 1 | `direct_form_input` | `field_accessible == True`, content < 10k | ★☆☆☆☆ |
| 2 | `direct_typing` | `editor_visible == True`, content < 5k | ★★☆☆☆ |
| 3 | `clipboard_paste` | `paste_supported == True` | ★★☆☆☆ |
| 4 | `file_upload` | `upload_available == True` | ★★★☆☆ |
| 5 | `scripting` | **Automation gate open only** | ★★★★★ |

---

## Automation Gate

```
OPEN (any one true):   frequency ≥ 5 · conditional_logic · transformation · external_integration
CLOSED (any one true): one_time + static · simpler_method_available · setup_time > run_time
```

When gate is CLOSED and ranks 1–4 all fail → notify user. Do NOT script.

---

## Verification (mandatory)

```
execute → visual_ok? ──no──→ refresh() → verify_programmatically(signature)
                                              ↓
                                    found? → ✅ complete
                                    missing → log + try next rank
```

**Never trust visual confirmation alone.**

---

## Lint Rules (pre-execution guard)

| Rule | What it catches |
|------|----------------|
| LINT-001 | Scripting chosen while simpler rank eligible |
| LINT-002 | `verification_required == False` — hard block |
| LINT-003 | Complexity bias (chosen rank > min eligible) |
| LINT-004 | Scripting for one-time static task |
| LINT-005 | No fallback chain defined (warning) |

---

## Package Contents

```
bin/skills/cidf/
├── SKILL.md                          ← this file (sub-skill)
├── FRAMEWORK.md                      ← canonical v1.2 spec
├── core/
│   ├── content_insertion_framework.py  ← decide(), verify(), execute_with_fallback()
│   ├── content_insertion_policy.json   ← machine policy + 6 test vectors
│   └── contentInsertionFramework.ts    ← TypeScript port
├── linter/
│   ├── policy_linter.py                ← LINT-001–005 guard
│   └── policyLinter.ts
└── tests/
    ├── test_conformance.py             ← 30 pytest tests (all must pass)
    └── conformance.test.ts
```

---

## Version Alignment (all must match)

| File | Must say |
|------|---------|
| This SKILL.md `version:` | `1.2.0` |
| `cidf/FRAMEWORK.md` header | `Version: 1.2` |
| `cidf/core/content_insertion_policy.json` → `framework_version` | `"1.2"` |
| `cidf/tests/test_conformance.py` assertion | `== "1.2"` |

**Never update the policy without bumping all four in the same commit.**

---

## Run Conformance Tests

```bash
pytest bin/skills/cidf/tests/test_conformance.py -v   # must be 30 passed, 0 failed
```
