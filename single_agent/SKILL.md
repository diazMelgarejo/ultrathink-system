---
name: ultrathink-system-skill
description: Master methodology for elegant problem solving. Unifies single_agent and multi_agent execution under the ultrathink 5-stage process. Routes automatically – runs inline for simple tasks (using CIDF v1.2 for any content insertion), escalates to the 7-agent network only when parallelism or scope demands it. Activates for any task requiring architectural thinking, systematic verification, content insertion decisions, or self-improvement.
version: 0.9.9.2
license: Apache 2.0
compatibility: claude-code, cowork, clawdbot, moltbot, openclaw, ecc-tools
allowed-tools: bash, file-operations, web-search, subagent-creation, mcp-ultrathink, mcp-ultrathink-lmstudio
---

# ultrathink System Skill

> *"Technology married with humanities yields solutions that make hearts sing.
> Every solution should feel inevitable — so elegant it couldn't be done any other way."*

---

## Execution Mode Router

> **First**: Run AFRP Gate (`single_agent/afrp/SKILL.md`) to classify query type before mode selection.

**This skill runs in one of three modes. The router decides automatically.**

```
Task arrives
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  ROUTER — evaluate three signals                        │
│  Signal 1: Content/data insertion involved?             │
│  Signal 2: Task complexity (steps, systems, parallel)   │
│  Signal 3: Explicit override from user                  │
└─────────────────────────────────────────────────────────┘
     │
     ├──► MODE 1: Inline Single-Agent     (simple, 1-2 steps)
     ├──► MODE 2: Single-Agent+Subagents  (standard, 3-7 steps)
     └──► MODE 3: Full Multi-Agent Net    (complex, 8+ steps / parallel)
```

### Router Decision Table

| Signal | Mode 1 — Simple | Mode 2 — Standard | Mode 3 — Complex |
|--------|-----------------|-------------------|-----------------|
| Steps | 1–2 | 3–7 | 8+ |
| Systems touched | 1 | 1–2 | 3+ |
| Parallel work needed | No | Maybe | Yes |
| Context window risk | Low | Medium | High |
| Codebase scope | File/function | Module | Multi-module/repo |
| User override | `--simple` | (default) | `--multi` |

**Override syntax**:
```
ultrathink --simple: fix this typo
ultrathink --multi: refactor auth across 3 services
ultrathink network: [task]
```

---

## Quick Start (v0.9.9.2)

Minimum viable LAN setup with LM Studio as the primary backend:

**Step 1 — Windows (UltraThink agent):**
```bash
# In LM Studio UI: load Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2-Q4_K_M.gguf
# Settings: GPU offload = 40 layers, context = 16384, server port = 1234
# Start LM Studio server
```

**Step 2 — Mac (orchestrator + validator):**
```bash
# In LM Studio UI: load Qwen3.5-9B-MLX-4bit (MLX tab)
# Settings: context = 4096 (conservative for M2), server port = 1234
# Start LM Studio server
```

**Step 3 — Environment:**
```bash
export LMS_WIN_ENDPOINTS=http://192.168.254.101:1234
export LMS_MAC_ENDPOINT=http://localhost:1234
export LMS_WIN_MODEL=Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2
export LMS_MAC_MODEL=Qwen3.5-9B-MLX-4bit
```

**Step 4 — Start services:**
```bash
python api_server.py      # ultrathink HTTP bridge on port 8001
python portal_server.py   # LAN dashboard on port 8002 (auto-refresh 10s)
```

**Step 5 — Verify:**
```bash
open http://localhost:8002   # portal shows all service statuses
curl http://localhost:8001/health  # api_server health check
```

> **Backend-agnostic note**: The GGUF/MLX model files loaded in LM Studio are compatible
> with Ollama, koboldcpp, and llama.cpp. Switching backends requires only an env var change.

## Content Insertion — CIDF v1.2 (All Modes, Always Active)

**Any time this skill inserts, writes, pastes, uploads, or scripts content — CIDF governs it.**
**No exceptions. No shortcuts. Start at rank 1 every time.**

### The One Rule
> Use the simplest tool that works. Complexity is a cost, not a feature.

### Method Priority

| Rank | Method | Eligible When | Complexity |
|------|--------|---------------|-----------|
| 1 | `direct_form_input` | Field accessible, content < 10k | ★☆☆☆☆ |
| 2 | `direct_typing` | Editor visible, content < 5k | ★★☆☆☆ |
| 3 | `clipboard_paste` | Paste supported, formatting OK | ★★☆☆☆ |
| 4 | `file_upload` | Upload available, format supported | ★★★☆☆ |
| 5 | `scripting` | **Automation gate passes only** | ★★★★★ |

### Automation Gate (before any script)

```
OPEN — scripting eligible (any one true):
  ✅ Repeats 5+ times  ✅ Conditional logic  ✅ Transformation  ✅ External integration

CLOSED — scripting blocked (any one true):
  ⛔ One-time + static content       ⛔ Simpler method available
  ⛔ Setup time > execution time     ⛔ All ranks 1-4 untried
```

### Verification Protocol (mandatory)

```
execute_method() → visual_ok? ──no──→ refresh_page()
                       ↓                     ↓
                       └──────────────→ verify_programmatically()
                                             ↓
                                 signature_in_page?
                                   yes → ✅ mark_complete()
                                   no  → log + try_next_rank()
```

### CIDF Runnable Package

Executable implementation in `cidf/` (same directory as this SKILL.md):

| File | Purpose |
|------|---------|
| `cidf/core/content_insertion_framework.py` | Python: `decide()`, `verify()`, `execute_with_fallback()` |
| `cidf/core/content_insertion_policy.json` | Machine policy + 6 test vectors (v1.2) |
| `cidf/core/contentInsertionFramework.ts` | TypeScript port |
| `cidf/linter/policy_linter.py` | LINT-001–005 CI guard (`lint_strict()`) |
| `cidf/tests/test_conformance.py` | 30 conformance tests — must all pass |
| `cidf/FRAMEWORK.md` | Canonical v1.2 specification |
| `references/content-insertion-framework.md` | Human reference v1.2 + cidf/ pointer |

**Quick usage (Python)**:
```python
from cidf.core.content_insertion_framework import Task, Env, decide
from cidf.linter.policy_linter import lint_strict
decision = decide(task, env)      # always starts at rank 1
lint_strict(decision, task, env)  # raises LintError on LINT-001–005
```

---

## MODE 1: Inline Single-Agent (Simple Tasks)

**When**: 1–2 steps, single file/function, content insertion if needed.

### Execution
1. Read context (30 seconds max)
2. **If content insertion**: `decide(task, env)` → use chosen rank → verify programmatically
3. Execute directly, no subagents
4. Verify result (Directive #4)
5. Done ✅

### Stays in Mode 1
Fix a typo · rename a variable · insert a content block · update a config value · answer a factual question

---

## MODE 2: Single-Agent + Subagents (Standard Tasks)

**When**: 3–7 steps. Apply full ultrathink 5-stage process inline.

### Stage 1 — Context Immersion
Scan project structure, git history, CLAUDE.md/AGENTS.md/SKILL.md files.
Identify constraints, patterns, idioms, historical lessons from `tasks/lessons.md`.
Output: 2–3 paragraph context summary.

### Stage 2 — Visionary Architecture
Design modular breakdown with clean interfaces.
**If content insertion involved → run CIDF `decide()` here** to select insertion method before any implementation begins.
Ask: "What would the most elegant solution look like?"

### Stage 3 — Ruthless Refinement
Apply quality rubric: simplicity ⭐⭐⭐⭐⭐, readability ⭐⭐⭐⭐⭐, robustness ⭐⭐⭐⭐.
Remove everything non-essential. Elegance = nothing left to take away.

### Stage 4 — Masterful Execution
```
Plan  → tasks/todo.md with checkable items
Craft → TDD, naming poetry, edge cases handled
CIDF  → every write/insert uses ranked method + programmatic verify
Verify→ python scripts/verify_before_done.py → must PASS
```

### Stage 5 — Crystallize the Vision
Assumptions ledger · simplification story · inevitability argument.
`python scripts/capture_lesson.py` if any corrections occurred.

### Subagent Delegation (Directive #2)
```python
# When context > 70% — offload, one task per subagent
subagent("Research best library for X. Return: comparison table.")
subagent("Prototype approach A"); subagent("Prototype approach B")
```

---

## MODE 3: Full Multi-Agent Network (Complex Tasks)

**When**: 8+ steps, parallel modules, cross-system, large codebase.
**Requires**: `python multi_agent/mcp_servers/ultrathink_orchestration_server.py`

### Agent Network
```
Orchestrator
  ├─► Context Agent       Stage 1 — parallel: doc scanner + git historian + pattern miner
  ├─► Architect Agent     Stage 2 — module design, spawns module-designer sub-agents
  ├─► Refiner Agent       Stage 3 — elegance loops (max 3 iterations, threshold 0.8)
  ├─► Executor Agents ×5  Stage 4 — parallel TDD; each calls CIDF before any write
  ├─► Verifier Agent      Stage 4.5 — blocks until PASS; enforces CIDF LINT-002
  └─► Crystallizer Agent  Stage 5 — docs + updates shared lessons DB
```

### CIDF Integration in Mode 3
Every **Executor Agent** calls `cidf/core/content_insertion_framework.py → decide()` before writing.
The **Verifier Agent** enforces LINT-002 (`verification_required == True`) as a hard gate.
The **Orchestrator** routes insertion tasks through CIDF-aware executor instances only.
Config: `multi_agent/config/agent_registry.json` · `multi_agent/config/routing_rules.json`

---

## The 6 Directives (Always Active, All Modes)

| # | Directive | Rule |
|---|-----------|------|
| 1 | **Plan Node** 📋 | `tasks/todo.md` before any 3+ step task |
| 2 | **Subagents** 🤖 | Offload when context > 70%; one task per subagent |
| 3 | **Self-Improve** 🔄 | After correction → `python scripts/capture_lesson.py` |
| 4 | **Verify First** ✅ | `scripts/verify_before_done.py` PASS required; no visual marking |
| 5 | **Elegance** ✨ | Pause on non-trivial: "Is there a more elegant way?" |
| 6 | **Autonomous Fix** 🔧 | Bug report → investigate → fix → verify → report; zero back-and-forth |

---

## Boundaries

### Always Do
- Run CIDF `decide()` before any content insertion (all modes, no exceptions)
- Verify programmatically after every insertion (CIDF protocol step 6)
- Write `tasks/todo.md` before implementing anything with 3+ steps
- Start at CIDF rank 1 — never jump directly to scripting

### Ask First
- Deleting files or directories
- Deploying to any live environment
- Modifying `config/`, `vendor/`, `.env` files
- Switching from Mode 2 → Mode 3 (resource cost)

### Never Do
- Mark complete without programmatic verification
- Skip CIDF for any content insertion (even "quick" writes)
- Trust visual confirmation alone
- Hardcode secrets or credentials
- Change `cidf/core/content_insertion_policy.json` without updating all 5 version locations

---

## Task Management

```
tasks/
├── todo.md      ← ./scripts/create_task_plan.sh "Task name"
├── lessons.md   ← python scripts/capture_lesson.py
└── archive/
```

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Token ROI | > 10:1 |
| CIDF compliance | 100% of insertions use ranked method + programmatic verify |
| Mode selection accuracy | Mode 3 used only when genuinely needed |
| Verification before done | 100% |
| Repeat mistake rate | < 5% (declining) |

---

*References: `cidf/FRAMEWORK.md` · `references/content-insertion-framework.md` · `references/ultrathink-5-stages.md` · `references/core-operational-directives.md`*

---
Note: The backup HTTP `/ultrathink` is implemented via `api_server.py` (v1.0 RC).
