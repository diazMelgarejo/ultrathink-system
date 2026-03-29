---
name: ultrathink-system-skill
description: Master methodology for elegant problem solving. Unifies single_agent and multi_agent execution under the ultrathink 5-stage process. Routes automatically – runs inline for simple tasks (using CIDF v1.2 for any content insertion), escalates to the 7-agent network only when parallelism or scope demands it. Activates for any task requiring architectural thinking, systematic verification, content insertion decisions, or self-improvement.
version: 0.9.8.0
license: Apache 2.0
compatibility: claude-code, cowork, clawdbot, moltbot, openclaw, ecc-tools
allowed-tools: bash, file-operations, web-search, subagent-creation, mcp-ultrathink
---

# ultrathink System Skill

> "Technology married with humanities yields solutions that make hearts sing. Every solution should feel inevitable — so elegant it couldn't be done any other way."

## Pre-Router Gate: AFRP (Mandatory)

**Before the Execution Mode Router fires, every non-trivial query passes through the Audience-First Response Protocol.**

```
Task arrives
│
▼
┌─────────────────────────────────────────────────────────┐
│ AFRP GATE — Audience-First Response Protocol            │
│ Sub-skill: afrp/SKILL.md                                │
│                                                         │
│ 1. Classify query type (A/B/C/D)                        │
│ 2. If B/C/D → ask max 2 clarifying questions            │
│ 3. Separate profile data from audience data              │
│ 4. Declare scope                                        │
│ 5. Calibrate abstraction level                          │
│ 6. Pass resolved context to Router                      │
└─────────────────────────────────────────────────────────┘
│
▼
Execution Mode Router (below)
```

**Load:** [`afrp/SKILL.md`](https://github.com/diazMelgarejo/ultrathink-system/blob/main/single_agent/afrp/SKILL.md) — always loaded first, before mode selection, before CIDF, before any agent bifurcation.

> Implements the Amplifier Principle: "Point it at clear intent and it accelerates you; point it at ambiguity and it scales the ambiguity."

## Execution Mode Router

**This skill runs in one of three modes. The router decides automatically.**

```
Task arrives
│
▼
┌─────────────────────────────────────────────────────────┐
│ ROUTER — evaluate three signals                         │
│                                                         │
│ Signal 1: Content/data insertion involved?              │
│ Signal 2: Task complexity (steps, systems, parallel)    │
│ Signal 3: Explicit override from user                   │
└─────────────────────────────────────────────────────────┘
│
├──► MODE 1: Inline Single-Agent (simple, 1-2 steps)
├──► MODE 2: Single-Agent+Subagents (standard, 3-7 steps)
└──► MODE 3: Full Multi-Agent Net (complex, 8+ steps / parallel)
```

### Router Decision Table

| Signal | Mode 1 — Simple | Mode 2 — Standard | Mode 3 — Complex |
| :--- | :--- | :--- | :--- |
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

## LAN Continuity & Reconciliation (Distributed State)

Since **v0.9.6.0**, ultrathink supports **LAN Detect & Resume** in coordination with **Perplexity-Tools**.

### LAN Resume Logic
* **Detect & Re-attach**: On startup, ultrathink checks for an existing session via local file-based state (`.state/session.log`).
* **Short Logging**: Maintains minimal state logs in `.state/session.log` to allow resumption of complex 5-stage reasoning processes after interruption.
* **Stateless by design**: ultrathink has no Redis dependency. All durable orchestration state (agent registry, budget tracking, distributed coordination) is owned by Perplexity-Tools. Redis-backed coordination is a future PT-only enhancement planned for v1.1+.

### Spawn Reconciliation (Layer 2 Coordination)
* **Global Registry Check**: Before spawning any sub-agent or worker, ultrathink MUST reconcile the spawn with the **Perplexity-Tools Orchestrator** (if available) to ensure proper session planning and model assignment.
* **Model-Aware Assignment**: Reconcile with the hardware registry to prevent GPU contention on machines like the `win-rtx3080` (Ollama/CUDA).
* **Efficient Operations**: Do not spawn new agents for subtasks if a matching idle agent exists in the global registry.

## Content Insertion — CIDF v1.2 (All Modes, Always Active)

**Any time this skill inserts, writes, pastes, uploads, or scripts content — CIDF governs it.**
**No exceptions. No shortcuts. Start at rank 1 every time.**

### The One Rule
> Use the simplest tool that works. Complexity is a cost, not a feature.

### Method Priority
| Rank | Method | Eligible When | Complexity |
| :--- | :--- | :--- | :--- |
| 1 | `direct_form_input` | Field accessible, content < 10k | ★☆☆☆ |
| 2 | `direct_typing` | Editor visible, content < 5k | ★★☆☆☆ |
| 3 | `clipboard_paste` | Paste supported, formatting OK | ★★☆☆☆ |
| 4 | `file_upload` | Upload available, format supported | ★★★☆☆ |
| 5 | `scripting` | **Automation gate passes only** | ★★★★ |

### Automation Gate (before any script)
```
OPEN — scripting eligible (any one true):
✅ Repeats 5+ times
✅ Conditional logic
✅ Transformation
✅ External integration

CLOSED — scripting blocked (any one true):
⛔ One-time + static content
⛔ Simpler method available
⛔ Setup time > execution time
⛔ All ranks 1-4 untried
```

### Verification Protocol (mandatory)
```
execute_method() → visual_ok? ──no──→ refresh_page()
                        ↓                   ↓
                        └──────────────→ verify_programmatically()
                                            ↓
                                    signature_in_page?
                                            yes → ✅ mark_complete()
                                            no  → log + try_next_rank()
```

### CIDF Runnable Package
**Sub-skill:** [`cidf/SKILL.md`](https://github.com/diazMelgarejo/ultrathink-system/blob/main/single_agent/cidf/SKILL.md) — load for full CIDF context, recursive sub-skill loading, and programmatic integration details.
Executable implementation in `cidf/` (same directory as this SKILL.md):

| File | Purpose |
| :--- | :--- |
| `cidf/core/content_insertion_framework.py` | Python: `decide()`, `verify()`, `execute_with_fallback()` |
| `cidf/core/content_insertion_policy.json` | Machine policy + 6 test vectors (v1.2) |
| `cidf/core/contentInsertionFramework.ts` | TypeScript port |
| `cidf/linter/policy_linter.py` | LINT-001–005 CI guard (`lint_strict()`) |
| `cidf/tests/test_conformance.py` | 30 conformance tests — must all pass |
| `cidf/FRAMEWORK.md` | Canonical v1.2 specification |
| `cidf/DESIGN.md` | Original design doc: flowcharts, decision matrices, meta-lesson |
| `references/amplifier-principle.md` | Foundational essay: why developers must stay in the driver's seat |
| `references/content-insertion-framework.md` | Human reference v1.2 + cidf/ pointer |

**Quick usage (Python)**:
```python
from cidf.core.content_insertion_framework import Task, Env, decide
from cidf.linter.policy_linter import lint_strict

decision = decide(task, env) # always starts at rank 1
lint_strict(decision, task, env) # raises LintError on LINT-001–005
```

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

## MODE 2: Single-Agent + Subagents (Standard Tasks)
**When**: 3–7 steps. Apply full ultrathink 5-stage process inline.

### Stage 1 — Context Immersion
* Scan project structure, git history, CLAUDE.md/AGENTS.md/SKILL.md files.
* Identify constraints, patterns, idioms, historical lessons from `tasks/lessons.md`.
* Output: 2–3 paragraph context summary.

### Stage 2 — Visionary Architecture
* Design modular breakdown with clean interfaces.
* **If content insertion involved → run CIDF `decide()` here** to select insertion method before any implementation begins.
* Ask: "What would the most elegant solution look like?"

### Stage 3 — Ruthless Refinement
Apply quality rubric:
* ⭐⭐⭐⭐⭐ simplicity,
* ⭐⭐⭐⭐⭐ readability,
* ⭐⭐⭐⭐⭐ robustness.
Remove everything non-essential. Elegance = nothing left to take away.

### Stage 4 — Masterful Execution
```
Plan  → tasks/todo.md with checkable items
Craft → TDD, naming poetry, edge cases handled
CIDF  → every write/insert uses ranked method + programmatic verify
Verify→ python scripts/verify_before_done.py → must PASS
```

### Stage 5 — Crystallize the Vision
Assumptions ledger · simplification story · inevitability argument. `python scripts/capture_lesson.py` if any corrections occurred.

### Subagent Delegation (Directive #2)
```python
# When context > 70% — offload, one task per subagent
subagent("Research best library for X. Return: comparison table.")
subagent("Prototype approach A"); subagent("Prototype approach B")
```

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
* Every **Executor Agent** calls `cidf/core/content_insertion_framework.py → decide()` before writing.
* The **Verifier Agent** enforces LINT-002 (`verification_required == True`) as a hard gate.
* The **Orchestrator** routes insertion tasks through CIDF-aware executor instances only.

Config: `multi_agent/config/agent_registry.json` · `multi_agent/config/routing_rules.json`

### autoresearch Integration (Mode 3 Task Type)
When the router detects `task_type == "autoresearch"`:
* **Execution**: Delegate to Perplexity-Tools `POST /autoresearch/sync` before any Mode 3 agent spawn.
* **Roles**: Three specialized agents (Coder / Evaluator / Orchestrator) orchestrated by Perplexity-Tools `AgentTracker`.
* **CIDF**: The **Coder** agent calls `decide()` before editing `train.py` → uses rank 2 (`direct_typing` on local file) followed by `scp` deployment.
* **Verification**: The **Evaluator** agent enforces LINT-002 (`verification_required == True`) by parsing `log.txt` programmatically (not visual confirmation).
* **Config**: `multi_agent/config/agent_registry.json` registers `autoresearch-coder`, `autoresearch-evaluator`, `autoresearch-orchestrator` as pre-defined agent types.

## The 6 Directives (Always Active, All Modes)

| # | Directive | Rule |
| :--- | :--- | :--- |
| 1 | 📋 **Plan Node** | `tasks/todo.md` before any 3+ step task |
| 2 | 🤖 **Subagents** | Offload when context > 70%; one task per subagent |
| 3 | 🔄 **Self-Improve** | After correction → `python scripts/capture_lesson.py` |
| 4 | ✅ **Verify First** | `scripts/verify_before_done.py` PASS required; no visual marking |
| 5 | ✨ **Elegance** | Pause on non-trivial: "Is there a more elegant way?" |
| 6 | 🔧 **Autonomous Fix** | Bug report → investigate → fix → verify → report; zero back-and-forth |

## Boundaries

### Always Do
* Run CIDF `decide()` before any content insertion (all modes, no exceptions)
* Verify programmatically after every insertion (CIDF protocol step 6)
* Write `tasks/todo.md` before implementing anything with 3+ steps
* Start at CIDF rank 1 — never jump directly to scripting

### Ask First
* Deleting files or directories
* Deploying to any live environment
* Modifying `config/`, `vendor/`, `.env` files
* Switching from Mode 2 → Mode 3 (resource cost)

### Never Do
* Mark complete without programmatic verification
* Skip CIDF for any content insertion (even "quick" writes)
* Trust visual confirmation alone
* Hardcode secrets or credentials
* Change `cidf/core/content_insertion_policy.json` without updating all 5 version locations

## Task Management
```
tasks/
├── todo.md         ← ./scripts/create_task_plan.sh "Task name"
├── lessons.md      ← python scripts/capture_lesson.py
└── archive/
```

## Success Criteria

| Metric | Target |
| :--- | :--- |
| Token ROI | > 10:1 |
| CIDF compliance | 100% of insertions use ranked method + programmatic verify |
| Mode selection accuracy | Mode 3 used only when genuinely needed |
| Verification before done | 100% |
| Repeat mistake rate | < 5% (declining) |

References: `afrp/SKILL.md` (sub-skill, pre-router gate) · `cidf/SKILL.md` (sub-skill, recursive) · `cidf/FRAMEWORK.md` · `cidf/DESIGN.md` · `references/amplifier-principle.md` · `references/content-insertion-framework.md` · `references/ultrathink-5-stages.md` · `references/core-operational-directives.md`

## Perplexity-Tools Orchestration Context

**When ultrathink-system is invoked via Perplexity-Tools orchestration, the following rules apply.**

ultrathink-system is Layer 2 in the 4-layer stack:
```
Perplexity-Tools (Layer 1) → ultrathink-system (Layer 2) → ECC Tools (Layer 3) → autoresearch (Layer 4)
```

### Priority Rule (Non-Negotiable)
* • **PT SKILL.md runs first** — PT owns top-level model selection and task routing
* • ultrathink is called **only when** `reasoning_depth=ultra` OR `privacy_critical=True`
* • Do **not** override PT's model selection for top-level agents
* • Only override when `reasoning_depth == ultra` and PT explicitly delegates

### Behavioral Constraints Under PT Orchestration
| Constraint | Rule |
| :--- | :--- |
| Model selection | Defer to PT's `config/routing.yml` for top-level models |
| Statelessness | ultrathink stays stateless; PT owns dedup via `.state/agents.json` |
| API endpoint | Serve via `api_server.py` on `POST /ultrathink` (port 8001) |
| Timeout | Respect `ULTRATHINK_TIMEOUT` env var (default: 120s) |
| Fallback | If Ollama unreachable, return HTTP 503; PT handles fallback to local qwen3:30b |

### Trigger Conditions (PT → ultrathink)
ultrathink is activated by PT routing when:
* • `task_type` matches `deep_reasoning` OR `code_analysis` in `config/routing.yml`
* • `privacy_critical=True` flag is set in the PT task payload
* • `reasoning_depth=ultra` is explicitly requested

### Integration References
* • Bridge spec: `docs/PERPLEXITY_BRIDGE.md`
* • Sync analysis: `docs/SYNC_ANALYSIS.md`
* • PT routing: `https://github.com/diazMelgarejo/Perplexity-Tools/blob/main/config/routing.yml`
* • PT SKILL.md: `https://github.com/diazMelgarejo/Perplexity-Tools/blob/main/SKILL.md`
* * • PT Hardware profiles: `https://github.com/diazMelgarejo/Perplexity-Tools/blob/main/hardware/SKILL.md` (mac-studio / win-rtx3080 model assignment matrix)

## Changelog

### v0.9.8.0 (2026-03-28)
* • **Hardware cross-link**: Added PT `hardware/SKILL.md` reference to Integration References.
* • **Version bump**: Aligned to v0.9.8.0 matching `api_server.py` (rate limiting, Pydantic V2 validators).

### v0.9.7.0 (2026-03-28)
* • **AFRP**: Audience-First Response Protocol integrated as mandatory pre-router gate (`afrp/SKILL.md`) [SYNC].
* • **Multi-agent alignment**: All 14 multi_agent subsystem files bumped from v0.9.4.3 to v0.9.7.0.
* • **CI hardening**: Standardized `setup-python@v5` across all workflows.

### v0.9.6.0 (2026-03-27)
* **LAN Continuity**: Synchronized **LAN Detect & Resume** logic with Perplexity-Tools.
* **Reconciliation**: Implemented **Layer 2 Spawn Reconciliation** to prevent redundant model spawns.
* **Distributed State**: File-based session state for local tracking; Redis deferred to PT-only (v1.1+).
* **Hardening**: Reinforced phase transitions to be resume-aware.
* **AFRP**: Integrated Audience-First Response Protocol as mandatory pre-router gate (`afrp/SKILL.md`).

### v0.9.4.3 (2026-03-24)
* Master methodology refinement and CIDF v1.2 standardization.
