---
name: ultrathink-system-skill
description: >-
  Elegant problem-solving methodology with 5-stage process, AFRP pre-router gate,
  CIDF v1.2 content insertion framework, and 7-agent execution network. Activates
  for architectural thinking, systematic verification, content insertion decisions,
  complex multi-step tasks, code quality reviews, and self-improvement workflows.
  Triggers on: "ultrathink", "think deeply", "5-stage", "systematic approach",
  "elegant solution", "verify before done", "content insertion", "AFRP", "CIDF".
version: 1.0.0
license: Apache 2.0
compatibility: claude-code, claude-desktop
allowed-tools: bash, file-operations, web-search, subagent-creation, mcp-ultrathink-lmstudio
sub_skills:
  - path: afrp/SKILL.md
    trigger: "Query is non-trivial, audience-dependent, or open-ended (Type B/C/D)"
  - path: cidf/SKILL.md
    trigger: "Any content insertion, file write, paste, upload, or scripted output"
---

# ultrathink System Skill

> "Technology married with humanities yields solutions that make hearts sing.
> Every solution should feel inevitable — so elegant it couldn't be done any other way."

## Pre-Router Gate: AFRP (Mandatory)

Before the Execution Mode Router fires, every non-trivial query passes through
the Audience-First Response Protocol.

```
Task arrives
    |
    v
+-- AFRP GATE (afrp/SKILL.md) -------------------------+
| 1. Classify query type (A/B/C/D)                      |
| 2. If B/C/D -> ask max 2 clarifying questions         |
| 3. Separate profile data from audience data            |
| 4. Declare scope                                       |
| 5. Calibrate abstraction level                         |
| 6. Pass resolved context to Router                     |
+--------------------------------------------------------+
    |
    v
Execution Mode Router (below)
```

> Implements the Amplifier Principle: "Point it at clear intent and it
> accelerates you; point it at ambiguity and it scales the ambiguity."

## Execution Mode Router

```
Task arrives (post-AFRP)
    |
    v
+-- ROUTER: evaluate three signals -----+
| Signal 1: Content insertion involved?  |
| Signal 2: Task complexity              |
| Signal 3: Explicit user override       |
+----|-----------|-------------|----------+
     v           v             v
  MODE 1      MODE 2        MODE 3
  Inline    + Subagents   Full Network
 (1-2 steps) (3-7 steps)  (8+ steps)
```

### Router Decision Table

| Signal              | Mode 1 Simple | Mode 2 Standard | Mode 3 Complex |
|---------------------|---------------|-----------------|----------------|
| Steps               | 1-2           | 3-7             | 8+             |
| Systems touched     | 1             | 1-2             | 3+             |
| Parallel work       | No            | Maybe           | Yes            |
| Context window risk | Low           | Medium          | High           |
| Codebase scope      | File/function | Module          | Multi-module   |

## Content Insertion — CIDF v1.2 (All Modes, Always Active)

**Any time this skill inserts, writes, pastes, uploads, or scripts content — CIDF governs it.**
No exceptions. Start at rank 1 every time.

### The One Rule
>
> Use the simplest tool that works. Complexity is a cost, not a feature.

### Method Priority

| Rank | Method             | Eligible When                      | Complexity |
|------|--------------------|------------------------------------|------------|
| 1    | `direct_form_input`| Field accessible, content < 10k    | 1          |
| 2    | `direct_typing`    | Editor visible, content < 5k       | 2          |
| 3    | `clipboard_paste`  | Paste supported, formatting OK     | 2          |
| 4    | `file_upload`      | Upload available, format supported  | 3          |
| 5    | `scripting`        | Automation gate OPEN only           | 5          |

### Verification Protocol (mandatory)

```
execute_method() -> visual_ok? --no--> refresh_page()
                       |                     |
                       +---> verify_programmatically()
                                    |
                             signature_in_page?
                               yes -> mark_complete()
                               no  -> try_next_rank()
```

Full CIDF details: `cidf/SKILL.md`

## MODE 1: Inline Single-Agent (Simple Tasks)

1. Read context (30 seconds max)
2. If content insertion: run CIDF `decide()` -> use chosen rank -> verify
3. Execute directly, no subagents
4. Verify result (Directive #4)
5. Done

## MODE 2: Single-Agent + Subagents (Standard Tasks)

### Stage 1 — Context Immersion

Scan project structure, git history, skill files. Identify constraints, patterns,
historical lessons. Output: 2-3 paragraph context summary.

### Stage 2 — Visionary Architecture

Design modular breakdown with clean interfaces. If content insertion -> run CIDF
`decide()` here. Ask: "What would the most elegant solution look like?"

### Stage 3 — Ruthless Refinement

Quality rubric: simplicity 5/5, readability 5/5, robustness 5/5.
Remove everything non-essential. Elegance = nothing left to take away.

### Stage 4 — Masterful Execution

```
Plan   -> tasks/todo.md with checkable items
Craft  -> TDD, naming poetry, edge cases handled
CIDF   -> every write/insert uses ranked method + programmatic verify
Verify -> scripts/verify_before_done.py -> must PASS
```

### Stage 5 — Crystallize the Vision

Assumptions ledger, simplification story, inevitability argument.
Run `scripts/capture_lesson.py` if any corrections occurred.

### Subagent Delegation (Directive #2)

```
When context > 70% -- offload, one task per subagent:
  subagent("Research best library for X. Return: comparison table.")
  subagent("Prototype approach A"); subagent("Prototype approach B")
```

## MODE 3: Full Multi-Agent Network (Complex Tasks)

### Agent Network

```
Orchestrator
+-> Context Agent       Stage 1 -- parallel: doc scanner + git historian
+-> Architect Agent     Stage 2 -- module design, spawns designers
+-> Refiner Agent       Stage 3 -- elegance loops (max 3, threshold 0.8)
+-> Executor Agents x5  Stage 4 -- parallel TDD; each calls CIDF before write
+-> Verifier Agent      Stage 4.5 -- blocks until PASS; enforces CIDF LINT-002
+-> Crystallizer Agent  Stage 5 -- docs + updates shared lessons DB
```

Config: `config/agent_registry.json` + `config/routing_rules.json`

### AutoResearch Integration (Mode 3 Task Type)

When the coordinating system reports **`task_type`** of **`autoresearch`** or **`ml-experiment`** (from **Perplexity-Tools**):

1. **Defer execution topology** to Perplexity-Tools: `POST /autoresearch/sync` must succeed (`sync_ok == true`) before deep multi-step planning assumes the GPU workspace is ready.
2. **Reasoning layer (this repo)**: apply **CIDF / ultrathink** methodology for hypotheses, critique, and next-step narrative — but **do not** assume cloud models for autoresearch unless the user explicitly overrides (see Perplexity-Tools `SKILL.md` “autoresearch Tasks”).
3. **GPU lock & metrics**: treat **`swarm_state.md`** (IDLE/BUSY) and **`log.txt` / `val_bpb`** as the source of truth for whether a run is active and whether metrics are valid.
4. **Cross-repo stack**: Perplexity-Tools (orchestrator) → ultrathink-system (reasoning) → ECC Tools (optional parallel executors) → Karpathy autoresearch loop on the GPU host.

For local setup work inside Perplexity-Tools, the Perplexity client now exposes optional `base_url` and `timeout` overrides, and the smoke-test script accepts the same values:

```bash
python scripts/test_perplexity.py --validate --base-url https://api.perplexity.ai --timeout 30
```


## The 6 Directives (Always Active, All Modes)

| # | Directive         | Rule                                                   |
|---|-------------------|--------------------------------------------------------|
| 1 | Plan Node         | Write `tasks/todo.md` before any 3+ step task          |
| 2 | Subagents         | Offload when context > 70%; one task per subagent      |
| 3 | Self-Improve      | After correction -> `scripts/capture_lesson.py`        |
| 4 | Verify First      | `scripts/verify_before_done.py` PASS required          |
| 5 | Elegance          | Pause on non-trivial: "Is there a more elegant way?"   |
| 6 | Autonomous Fix    | Bug report -> investigate -> fix -> verify -> report   |

## Boundaries

### Always Do

- Run CIDF `decide()` before any content insertion (all modes, no exceptions)
- Verify programmatically after every insertion
- Write `tasks/todo.md` before implementing anything with 3+ steps
- Start at CIDF rank 1 — never jump directly to scripting

### Ask First

- Deleting files or directories
- Deploying to any live environment
- Modifying config, vendor, or .env files
- Switching from Mode 2 -> Mode 3 (resource cost)

### Never Do

- Mark complete without programmatic verification
- Skip CIDF for any content insertion (even "quick" writes)
- Trust visual confirmation alone
- Hardcode secrets or credentials

## Success Criteria

| Metric                    | Target |
|---------------------------|--------|
| Token ROI                 | > 10:1 |
| CIDF compliance           | 100%   |
| Mode selection accuracy   | Mode 3 only when genuinely needed |
| Verification before done  | 100%   |
| Repeat mistake rate       | <5%   |

## Quick Start (Usage Guide)

### 1. Activation

Trigger the full 5-stage process with:

- `ultrathink this`
- `apply the system to: [your task]`
- `production-ready [task]`

### 2. Mandatory Workflow

Follow the 6 directives in every non-trivial task:

1. **Plan**: `./scripts/create_task_plan.sh "Build feature"`
2. **Execute**: Build stage-by-stage (Context -> Architect -> Refine -> Execute -> Crystallize)
3. **Verify**: `python scripts/verify_before_done.py` (Must PASS before done)
4. **Learn**: `python scripts/capture_lesson.py` (Run after any correction)

### 3. Integrated Frameworks

- **AFRP**: Pre-router gate. Classifies and clarifies intent before architecture.
- **CIDF v1.2**: Content insertion governance. Start at rank 1 (direct_form_input) for every write.

> **Historical Note:** The legacy backup HTTP `/ultrathink` is implemented via `api_server.py` for v1.0 compatibility.

## OpenClaw Multi-Agent Bridge (Tier 2)

Use the `mcp-ultrathink-openclaw` tool to offload heavy reasoning through the
OpenClaw gateway at `127.0.0.1:18789`. Model selection is automatic — OpenClaw
reads `~/.openclaw/openclaw.json` and routes each `agent_id` to the correct
live provider (LM Studio / Ollama, Mac / Windows GPU).

### Capabilities

- `openclaw_chat`: Route by role (`coder`, `orchestrator`, `mac-researcher`, `win-researcher`)
- `openclaw_list_agents`: List agents registered in `~/.openclaw/openclaw.json`
- `openclaw_orchestrate`: Dispatch Stage 4 execution tasks via OpenClaw gateway
- `openclaw_health`: Verify gateway is running at `127.0.0.1:18789`

## References (Progressive Disclosure)

Load on demand for deeper context:

- `afrp/SKILL.md` — Audience-First Response Protocol (pre-router gate)
- `cidf/SKILL.md` — Content Insertion Decision Framework v1.2
- `references/amplifier-principle.md` — foundational essay on intent-driven development
- `references/ultrathink-5-stages.md` — deep dive on the 5-stage methodology
- `references/core-operational-directives.md` — the 6 directives in detail
- `references/content-insertion-framework.md` — CIDF human reference + JSON policy
- `references/skill-architecture-guide.md` — how to build SKILL.md files
- `templates/task-plan.md` — task planning template (Directive #1)
- `templates/verification-checklist.md` — pre-completion checklist (Directive #4)
- `templates/lessons-log.md` — self-improvement log (Directive #3)
