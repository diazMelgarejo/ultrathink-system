# RC-1 Master Orchestration Plan — Parallel Agent Dispatch

**Date:** 2026-05-14
**Target version:** v1.0.0.0 RC-1 (do NOT bump version — previous agent already did premature bump)
**Status:** Planning only — NO execution until user approves the dispatch design
**Source goals:** `/Users/lawrencecyremelgarejo/Documents/Terminal xCode/claude/OpenClaw/v1/Organized-Goals.md`
**Source defaults:** `/Users/lawrencecyremelgarejo/Documents/Terminal xCode/claude/OpenClaw/v1/OpenRouter.md`

---

## 1. Situational snapshot (as-found 2026-05-14)

### Source files for MCP consolidation
| File | Bytes | Role |
|------|-------|------|
| `~/.claude/skills/mcp-orchestration/SKILL.md` | 16,874 | Live canonical skill (likely best content) |
| `OpenClaw/MCP_ORCHESTRATION_SKILL.md` | ? | v1 source (merge target) |
| `OpenClaw/MCP_ORCHESTRATION_SKILL_v2.md` | ? | v2 source (preserve as primary) |
| `OpenClaw/MCP-INSTALL-PLAN.md` | ? | Companion install plan |
| `orama-system/bin/orama-system/mcp-install/SKILL.md` | ? | Existing sibling skill that REFERENCES the orchestration doc |

**Canonical target:** `orama-system/bin/orama-system/mcp-orchestration/SKILL.md` (directory MUST be created)

### openclaw.json files to patch with OpenRouter defaults
1. `~/.openclaw/openclaw.json` (live config — patch with `--apply-live` flag)
2. `OpenClaw/alphaclaw-observability/config/openclaw.json` (lab config)
3. `OpenClaw/AlphaClaw/lib/onboarding/defaults/openclaw.json.template` (default for new installs)

**SKIP:** `AlphaClaw/lib/plugin/usage-tracker/openclaw.plugin.json` (plugin config, different schema), `wrong/AlphaClaw-corrupted/*` (quarantined).

### Backend / frontend state
- Backend FastAPI routes already exist in `portal_server.py`:
  - `GET /api/app/state` (line 1497)
  - `POST /api/swarm/preview` (line 1532)
  - `POST /api/swarm/launch` (line 1538)
  - Plus jobs/artifacts proxy routes (per Organized-Goals.md)
- Backend tests already exist (`tests/test_swarm_launch.py`, `tests/test_portal_app_state.py`)
- **Vite React app does NOT exist** — no `package.json`, `vite.config.*`, or `src/` at repo root. Must scaffold fresh.

### Branch state (important)
- Current branch: `web-app-orchestration-v2-implementation`
- 4 commits ahead of main (salvage spec, claude auth lesson, swarm preview APIs, app state APIs)
- 0 commits behind main
- **Decision:** Continue all RC-1 work on this branch. Final merge to main happens at end of Stage 7 (or via PR).

### Version constraint
- Current version: `0.9.9.8` (in CLAUDE.md `@diazmelgarejo/orama-system@0.9.9.8`)
- Target: `v1.0.0.0 RC-1`
- **Hard rule: do NOT bump version in any intermediate commit.** Final version bump happens only at Stage 7 close.

---

## 2. Agent dispatch matrix (per OpenRouter.md new order)

Per Organized-Goals.md Goal 4 + OpenRouter.md §5 (new priority order — Gemini pushed to 3rd):

| Agent | Where it runs | Strengths | Use for |
|-------|---------------|-----------|---------|
| **Local ollama qwen3.5** (Mac, `localhost:11434`) | Local hardware | Free, private, fast, no network dependency | Lint, format, local file validation, ROUTINE bash scripts |
| **OpenRouter Nemotron 3 Super (1M ctx, free)** | OpenRouter API | Strong agent profile, long context, SWE-Bench | Long-context audits, agent reasoning, large-file review |
| **OpenRouter MiniMax M2.5 (205K, free)** | OpenRouter API | 80.2% SWE-Bench Verified | TypeScript/React coding, multi-file plans |
| **OpenRouter DeepSeek V4 Flash (1M, free)** | OpenRouter API | Fast, high-throughput | Triage, heartbeat-style checks, fast lookups |
| **OpenRouter gpt-oss-120b (131K, free)** | OpenRouter API | Strong tool use, structured output | Structured-output tasks, second-opinion critique |
| **Codex CLI** | Subprocess via ai-cli-mcp | Mechanical TypeScript/Python edits, file patching | Search-replace, JSON patching, boilerplate generation |
| **Gemini CLI** | Subprocess via gemini-mcp-tool | 2M-token context window | **DOWNGRADED to 3rd-choice review (GitHub access issues per user note)** |
| **Claude Sonnet 4.6 medium + prompt caching** | This session | Judgment, final synthesis, content insertion decisions | Reviews, taste calls, commit messages, conflict resolution |

**Token economy rule:** the lowest-capability agent that can succeed gets the task. Save Sonnet 4.6 for judgment and synthesis ONLY.

**Prompt caching rule (Goal 2):** all Claude Sonnet 4.6 calls in this session use `cache_control` on stable system/tool/context prefixes. Never cache changing suffixes (timestamps, per-run user payloads).

---

## 3. The 7-stage execution plan

### Stage 0 — Pre-flight verification (no agents, this session, 2 min)
- [ ] Confirm branch is `web-app-orchestration-v2-implementation`
- [ ] Confirm 4 commits ahead of main
- [ ] Confirm OPENROUTER_API_KEY env var is set (or fail loud)
- [ ] Read MCP_ORCHESTRATION_SKILL.md byte counts to inform reader-agent budgeting

---

### Stage 1 — MCP Orchestration Consolidation (Goal 1 + Goal 2)
**Sequential within stage; Stage 1 + Stage 2 run in PARALLEL across the two parallel groups below.**

**Inputs:**
- `~/.claude/skills/mcp-orchestration/SKILL.md` (16.8KB — likely best content)
- `OpenClaw/MCP_ORCHESTRATION_SKILL.md` (v1)
- `OpenClaw/MCP_ORCHESTRATION_SKILL_v2.md` (v2 — preserve as primary)
- `OpenClaw/MCP-INSTALL-PLAN.md` (companion)
- `orama-system/bin/orama-system/mcp-install/SKILL.md` (sibling that references both)

**Output:** `orama-system/bin/orama-system/mcp-orchestration/SKILL.md` (canonical)

**Tasks and agent assignment:**

| Step | Task | Agent | Why |
|------|------|-------|-----|
| 1a | **Audit references** — find all backlinks/linkbacks to either MCP_ORCHESTRATION doc across `orama-system/`, `AlphaClaw/`, `Perpetua-Tools/`, `alphaclaw-observability/` | **Nemotron 3 Super (OpenRouter)** | 1M ctx, agent reasoning, free |
| 1b | **Build canonical SKILL.md** — merge v2 (primary) + v1 (drift-removed) + user-level skill, add Claude auth lesson section | **Claude Sonnet 4.6 + prompt caching** | Judgment task: deciding what to preserve, what's drift |
| 1c | **Add Claude prompt-caching policy** — cite Anthropic docs, model = `claude-sonnet-4-6`, thinking = medium, cache stable prefixes only | **Claude Sonnet 4.6** | Self-documenting policy — model knows its own constraints |
| 1d | **Update linkbacks** — rewrite all references found in 1a to point to `bin/orama-system/mcp-orchestration/SKILL.md`; turn root MCP_ORCHESTRATION_SKILL.md and _v2.md into 5-line redirect stubs | **Codex CLI** | Mechanical search-replace across many files |

**Parallel candidates within stage:** 1a (read-only) runs concurrently with 1b–1c (write to single file). 1d runs ONLY after 1a returns the reference list.

---

### Stage 2 — OpenRouter merge (parallel with Stage 1)
**Independent files; can run concurrently with Stage 1 entirely.**

**Tasks:**

| Step | Task | Agent | Why |
|------|------|-------|-----|
| 2a | **Generate `scripts/apply-openrouter-free-defaults.sh`** — idempotent JSON patcher per OpenRouter.md §8 | **ollama qwen3.5** (local Mac) | Bash scripting, local, free |
| 2b | **Generate `scripts/verify-openrouter-models.sh`** — endpoint smoke test per OpenRouter.md §9 | **ollama qwen3.5** (local) | Bash, local |
| 2c | **Generate `deployments/macbook-pro-head/openclaw/openclaw.model-policy.jsonc`** — canonical patch (per OpenRouter.md §6, with reordered preferences: ollama 1st, OpenRouter 2nd, Gemini 3rd) | **Codex CLI** | Mechanical JSONC generation |
| 2d | **Patch `~/.openclaw/openclaw.json`** — apply OpenRouter defaults, preserve gateway/WhatsApp/sandbox | **Codex CLI** | Mechanical JSON patching with backups |
| 2e | **Patch `alphaclaw-observability/config/openclaw.json`** | **Codex CLI** | Mechanical |
| 2f | **Patch `AlphaClaw/lib/onboarding/defaults/openclaw.json.template`** | **Codex CLI** | Mechanical |
| 2g | **Create `docs/OPENROUTER_FREE_MODELS.md`** — short reference doc per OpenRouter.md §13 (changelog entry) | **MiniMax M2.5** (OpenRouter) | Coding-doc writing |
| 2h | **Verify** — run the verification script, confirm endpoint checks pass | **Local bash** (no agent) | Direct execution |

**Critical OpenRouter.md adjustment per user instruction:** the default fallback ORDER changes from OpenRouter.md §5 to insert **local ollama** as primary and **Gemini** as 3rd-choice review (downgraded due to GitHub access issues):

```text
NEW ORDER (this session):
1. ollama qwen3.5 (Mac local)          ← was implied as separate
2. openrouter/nvidia/nemotron-3-super... ← was #1 in OpenRouter.md
3. openrouter/minimax/minimax-m2.5...
4. openrouter/deepseek/deepseek-v4...
5. openrouter/openai/gpt-oss-120b...
6. openrouter/z-ai/glm-4.5-air...
7. openrouter/inclusionai/ling-2.6-flash...
8. openrouter/openrouter/free
9. gemini (3rd-choice review only)        ← was #1 reader before
```

---

### Stage 3 — Commit foundation (after Stages 1 + 2 done)
- [ ] Stage all created/modified files
- [ ] Single commit: "feat(rc1): consolidate MCP orchestration + OpenRouter free-model defaults"
- [ ] Push to `web-app-orchestration-v2-implementation`

**Agent:** Claude Sonnet 4.6 (judgment for commit message, no caching needed here)

---

### Stage 4 — Vite React Operator Console (Goal 3)
**Depends on Stage 3 commit.**

**Layout (per Organized-Goals.md visual target):**
```
src/
├── api/                          ← backend clients
│   ├── appState.ts               ← GET /api/app/state
│   ├── swarm.ts                  ← POST /api/swarm/preview, /api/swarm/launch
│   ├── jobs.ts                   ← jobs list/detail/cancel/replay proxy
│   └── artifacts.ts              ← artifacts proxy
├── features/
│   └── command-center/
│       ├── CommandCenter.tsx     ← page composition
│       ├── ReadinessStrip.tsx
│       ├── SwarmComposer.tsx
│       ├── WorkerAssignments.tsx
│       ├── RunsTable.tsx
│       └── ArtifactsPanel.tsx
├── components/                   ← reusable primitives
│   ├── Shell.tsx
│   ├── Table.tsx
│   ├── StatusBadge.tsx
│   ├── EnvBar.tsx
│   └── NavLeft.tsx
├── data/
│   └── mockState.ts              ← fallback/dev seed only
├── styles/
│   └── tokens.css                ← dark console CSS tokens
└── main.tsx
```

**Tasks:**

| Step | Task | Agent | Why |
|------|------|-------|-----|
| 4a | **Scaffold Vite + React + TypeScript** at orama-system repo root (`npm create vite@latest .`-style or manual `package.json`/`vite.config.ts`) | **Claude Sonnet 4.6** | Structure decisions, choose deps (TanStack Query? plain fetch? CSS framework?) |
| 4b | **Create API clients in `src/api/`** — typed fetch wrappers for the 4 route groups | **Codex CLI** | TypeScript boilerplate |
| 4c | **Create `src/components/` primitives** — Shell, Table, StatusBadge, EnvBar, NavLeft per visual target | **MiniMax M2.5** (OpenRouter) | Coding model, 205K ctx |
| 4d | **Create `src/features/command-center/` page + sub-components** | **MiniMax M2.5** | Coding model |
| 4e | **Create `src/styles/tokens.css`** — dark console design tokens (colors, spacing, typography) | **ollama qwen3.5** (local) | Simple CSS, no network |
| 4f | **Create `src/data/mockState.ts`** — fallback seed data matching backend shapes | **Codex CLI** | Mechanical from backend types |

**Parallel groups within Stage 4:**
- After 4a: 4b, 4c, 4d, 4e, 4f all touch DIFFERENT directories — **all run in parallel**.

---

### Stage 5 — Tests + Build
**Depends on Stage 4.**

| Step | Task | Agent | Why |
|------|------|-------|-----|
| 5a | Frontend lint (`npm run lint`) | **ollama qwen3.5** (local) | Local execution |
| 5b | Frontend type-check (`npm run typecheck` / `tsc --noEmit`) | **ollama qwen3.5** (local) | Local |
| 5c | Frontend build (`npm run build`) | **ollama qwen3.5** (local) | Local |
| 5d | Backend pytest (existing tests stay green) | **Local pytest** | No agent — direct execution |
| 5e | Triage any failures | **Claude Sonnet 4.6 + cache** | Judgment on what to fix |

---

### Stage 6 — Dev server + browser verification
| Step | Task | Agent | Why |
|------|------|-------|-----|
| 6a | Start dev server (`npm run dev`) in background | **Local bash** | Direct |
| 6b | Visual comparison against screenshot target | **Gemini CLI** (its #1 strength is large visual context) | EXCEPTION to "Gemini 3rd-choice" rule — visual sandbox is its specialty |
| 6c | Capture any visual deltas, fix | **MiniMax M2.5** | Coding model |

---

### Stage 7 — Final commit + close (Execution Order 10)
- [ ] Commit frontend implementation
- [ ] Update CHANGELOG (do NOT bump version — leave at 0.9.9.8)
- [ ] Push to `web-app-orchestration-v2-implementation`
- [ ] Optionally: open PR to main

**Agent:** Claude Sonnet 4.6

---

## 4. Token-economy budget

Per "use the least amount of tokens like we did last time":

| Resource | Estimated tokens this session | Notes |
|----------|-------------------------------|-------|
| Claude Sonnet 4.6 (judgment + reviews) | ~30K total | Prompt-cache stable system prefix saves ~60% on repeat calls |
| Local ollama qwen3.5 | 0 API tokens | Free, runs on Mac |
| OpenRouter free models (Nemotron, MiniMax, etc.) | 0 API tokens | Free tier — 50 req/day per OpenRouter.md §2 |
| Codex CLI | Bounded by Codex's own subscription | Use ai-cli-mcp PID tracking to monitor |
| Gemini CLI | Minimal — only Stage 6b visual diff | Per user note: pushed to 3rd-choice |

**Budget guard:** if any agent exceeds expected work-size (e.g., a Codex worker hangs >5 min), kill its PID via `ai-cli-mcp kill_process` and re-dispatch with narrower scope.

---

## 5. Acceptance gates

Before this plan is declared done:

- [ ] Stage 1 acceptance: canonical SKILL.md exists at `bin/orama-system/mcp-orchestration/SKILL.md` with Claude auth lesson + prompt caching section; root MCP_ORCHESTRATION docs are redirect stubs; all linkbacks updated
- [ ] Stage 2 acceptance: `apply-openrouter-free-defaults.sh` runs idempotently; `~/.openclaw/openclaw.json` contains OpenRouter primary+fallbacks AND preserves gateway/WhatsApp/sandbox per OpenRouter.md §12 acceptance tests
- [ ] Stage 4 acceptance: `npm run build` exits 0; bundle size <500KB gzipped
- [ ] Stage 5 acceptance: all existing backend tests green; frontend lint clean
- [ ] Stage 6 acceptance: dev server starts, Gemini visual diff returns <5 mismatches from screenshot target
- [ ] Version is STILL `0.9.9.8` (no premature bump)
- [ ] All work on `web-app-orchestration-v2-implementation` branch

---

## 6. Risks and unknowns

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| OpenRouter free-tier rate limits hit (50 req/day) | Medium | Use Codex/ollama as primary; OpenRouter as secondary fallback |
| MCP_ORCHESTRATION docs have already drifted to different copies in unknown locations | Medium | Stage 1a Nemotron audit will surface them all; if so, expand Stage 1d scope |
| Vite scaffold conflicts with existing `bin/`/`tests/` Python layout | Low | Scaffold at repo root; Vite's `src/` and `public/` don't collide with Python layout |
| Backend route contracts don't match Organized-Goals.md spec exactly | Medium | Stage 4a reads `portal_server.py` first to ground API client types |
| Branch divergence (web-app-orchestration-v2-implementation vs main) creates merge conflicts later | Low | Defer merge to a separate PR-creation task after Stage 7 |
| OPENROUTER_API_KEY not set on machine | High | Stage 0 pre-flight check fails loud; user must set key before Stage 2 starts |

---

## 7. Locked decisions (user-approved 2026-05-14)

1. **OPENROUTER_API_KEY**: ✅ Set. Stage 2 proceeds with live patching.
2. **Vite stack**: 🔒 **React + TanStack Query + Tailwind CSS**. Decided upfront — no Stage 4a stack debate.
3. **Gemini routing policy (PERMANENT — to be encoded in canonical SKILL.md):**
   > **Default routing:** OpenRouter free models + fallbacks (per §2 matrix).
   > **Gemini-Analyzer use-case routing:** Use Gemini ONLY when caller explicitly specifies a "Gemini-Analyzer" task. These use-cases include: large-context document review, screenshot/visual diff, code review of large files, multi-file architecture audits.
   > **Stage 6b (visual diff vs screenshot target):** Falls under Gemini-Analyzer use-case → use Gemini.
   > **Why this matters:** OpenRouter.md §0 says "don't blanket-route via Gemini" due to GitHub access issues. But Gemini's 2M-context vision sandbox is unique. Reserve it for tasks where its specialty matters; default to OpenRouter for everything else.
4. **Branch merge timing**: 🔒 Merge `web-app-orchestration-v2-implementation` → main **after Stage 3 commit** (foundation done). Stage 4+ continues on the same branch and gets its own merge later.

These decisions are durable — they will be reflected in the canonical `bin/orama-system/mcp-orchestration/SKILL.md` so future sessions inherit them.

---

## 8. What this plan does NOT include (deferred)

- Salvage spec from earlier session (already committed: `2026-05-14-salvage-plugins-design.md`) — Phase 2 of v2 oramasys work, separate brainstorm session
- Phase 2 oramasys engine changes (`set_entry`, `compile`, max_steps guard)
- Any version bump to v1.0.0.0 (deferred to RC-1 close)
- PR creation (deferred; can be a follow-up task)
