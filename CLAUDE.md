# orama-system — Claude Code Navigation

> Renamed: ultrathink-system → orama-system (2026-04-20, ὅραμα = "that which is seen / vision / revelation")
> Package: `@diazmelgarejo/orama-system@0.9.9.8`
> GitHub: <https://github.com/diazMelgarejo/orama-system>

---

## Meta-rule: Progressive Disclosure (Horse Pulls Cart)

**Documents own content. This file navigates.**

> "The horse pulls the cart, not the other way around."

- When in doubt: read the doc, don't restate it here.
- This file's job is routing + constraints. Docs are the source of truth.
- Skills operationalize docs — they don't copy them.
- Full instructions → [`../CLAUDE-instru.md`](../CLAUDE-instru.md)

---

## § 0 — Architectural Contracts

**Source of truth:** [`docs/2026-05-14--UNIFIED-ABSORPTION-PLAN.md`](docs/2026-05-14--UNIFIED-ABSORPTION-PLAN.md) §§ 0–2.
Read before any structural change. Below is a navigation summary only.

| Topic | Where |
|-------|-------|
| Banned terminology (coordinator → orchestrator, etc.) | [§ 1 / Terminology](docs/2026-05-14--UNIFIED-ABSORPTION-PLAN.md#-1--governing-principles-non-negotiable) |
| 8 governing principles | [§ 1](docs/2026-05-14--UNIFIED-ABSORPTION-PLAN.md#-1--governing-principles-non-negotiable) |
| **Hard requirements** (Mac: Ollama + qwen3.5:9b-nvfp4 + bge-m3; Win: LM Studio) | [§ 2 / Hardware](docs/2026-05-14--UNIFIED-ABSORPTION-PLAN.md) · [`../CLAUDE-instru.md § 6`](../CLAUDE-instru.md) |
| Shared types (all 5 live in PT's `orchestrator/contracts.py`) | [§ 2 / Types](docs/2026-05-14--UNIFIED-ABSORPTION-PLAN.md) |
| Verifier gate (crystallization blocked without approved result) | [§ 2 / Gates](docs/2026-05-14--UNIFIED-ABSORPTION-PLAN.md) |
| V1 scope boundary (MAESTRO/HITL deferred) | [§ 2 / V1](docs/2026-05-14--UNIFIED-ABSORPTION-PLAN.md) |
| HITL accountability classes | [`docs/HUMAN-IN-LOOP-ACCOUNTABILITY.md`](docs/HUMAN-IN-LOOP-ACCOUNTABILITY.md) |

**Quick invariants (full detail in doc above):**
- `orchestrator` only — never `coordinator` in public APIs, schemas, config, or headings
- PT is runtime/state authority; orama is **stateless** methodology
- **Mac hard requirements:** Ollama running (`localhost:11434`) with `qwen3.5:9b-nvfp4` (inference) + `bge-m3` (embeddings) — system does not start without these
- **Win hard requirement:** LM Studio at `$LM_STUDIO_WIN_ENDPOINTS` — no fallback; fail loudly if unavailable
- **Everything else optional:** LM Studio Mac, cloud APIs, other local models
- One heavy model at a time on Windows GPU
- `@field_validator` (Pydantic V2) — never deprecated `@validator`
- `depth=0` validated server-side; workers cannot spawn sub-workers in V1

---

## § 1 — Continuous Learning

Every session: read [`docs/LESSONS.md`](docs/LESSONS.md) at start; append discoveries before exit.
Instinct path: `.claude/homunculus/instincts/inherited/orama-system-instincts.yaml`
Full spec: [continuous-learning-v2](https://github.com/affaan-m/everything-claude-code/tree/main/skills/continuous-learning-v2)

---

## § 2 — ECC Post-Merge Workflow

After any ECC Tools PR merges:

```bash
git pull origin main
# Then in Claude Code:
/instinct-import .claude/homunculus/instincts/inherited/orama-system-instincts.yaml
/instinct-status
git add -A && git commit -m "chore(ecc): post-merge instinct import sync" && git push origin main
```

Or: `/ecc-sync` (`.claude/commands/ecc-sync.md`)

---

## § 3 — Agent Skills & Mother Skill

Before significant changes, load the mother skill:

```claude
/skill bin/orama-system/SKILL.md
```

| Resource | Purpose |
|----------|---------|
| [`SKILL.md`](SKILL.md) | Agent behavioral rules — every "never" with commands |
| [`bin/orama-system/SKILL.md`](bin/orama-system/SKILL.md) | Mother skill: AFRP gate, CIDF, gstack routing |
| [`docs/LESSONS.md`](docs/LESSONS.md) | Chronological session log |
| [`docs/wiki/README.md`](docs/wiki/README.md) | Wiki index — lesson deep-dives |

---

## § 4 — Three-Repo Architecture

```
AlphaClaw (L1 — infra) → Perpetua-Tools (L2 — middleware) → orama-system (L3 — THIS REPO — orchestration)
```

Full architecture: [`docs/2026-05-14--UNIFIED-ABSORPTION-PLAN.md`](docs/2026-05-14--UNIFIED-ABSORPTION-PLAN.md)
Current as-built: [`docs/v2/`](docs/v2/)
Path map (harness/skill locations): see `§ 8` of the archived full CLAUDE.md in [`docs/archive/`](docs/archive/)

**Critical invariants:**
- `start.sh` delegates gateway decisions to PT's `orchestrator/alphaclaw_manager.py` — never add routing logic to `start.sh`
- orama API stays stateless (no Redis)
- orama talks to AlphaClaw through PT's adapter, never directly

---

## § 5 — AutoResearcher

Plugin: `uditgoenka/autoresearch`. Activate per-session: `/autoresearch`.
Read + write [`docs/LESSONS.md`](docs/LESSONS.md) around experiment runs.
Full setup: [`docs/wiki/06-multi-agent-collab.md`](docs/wiki/06-multi-agent-collab.md)

---

## § 6 — Repository Identity & Git Hygiene

- Commit identity: `cyre <Lawrence@cyre.me>` or `Codex <codex@openai.com>` — verify with `bash scripts/git/check_identity.sh`
- Dated branches: `yyyy-mm-dd-NNN-brief-summary`
- Never commit `.env`, `.env.local`, generated `.paths`
- Full rules: [`docs/wiki/08-git-hygiene-and-branching.md`](docs/wiki/08-git-hygiene-and-branching.md)

---

## § 7 — gstack

gstack v1.37.0.0 at `~/.claude/skills/gstack` (global-git).

Safety rules:
- ALWAYS use `/browse` for web — NEVER `mcp__claude-in-chrome__*` directly
- `/investigate` for root-cause; `/ship` before any publish

Load routing table + GBrain config:
```
/skill bin/orama-system/gstack/SKILL.md
```

---

## § 8 — Next Stage: Semantic Memory (bge-m3 / Ollama)

gbrain is now fully indexed with **Ollama bge-m3** (local, free, 1024-dim vector).
See [`../CLAUDE-instru.md § 5`](../CLAUDE-instru.md) for the full next-stage plan.

**Current state (2026-05-15):**
- Embedding: `ollama:bge-m3` (1024 dims) — `~/.gbrain/config.json`
- Backend: Supabase PostgreSQL via Session Pooler (port 6543)
- 9,510/9,510 chunks embedded across 1,153 pages
- Storage roadmap **decided** (2026-05-15) — see [`../CLAUDE-instru.md § 5`](../CLAUDE-instru.md):
  - v2.1: LanceDB + bge-m3 for RAG/session memory; v2.5: DuckDB for fleet analytics
  - gbrain (pgvector) = codebase index; LanceDB = orama job/decision history — these coexist

---

## GBrain Search Guidance (configured by /sync-gbrain)
<!-- gstack-gbrain-search-guidance:start -->

GBrain is set up and synced on this machine. The agent should prefer gbrain
over Grep when the question is semantic or when you don't know the exact
identifier yet.

**This worktree is pinned to a worktree-scoped code source** via the
`.gbrain-source` file in the repo root (kubectl-style context). Any
`gbrain code-def`, `code-refs`, `code-callers`, `code-callees`, or `query`
call from anywhere under this worktree routes to that source by default —
no `--source` flag needed.

Two indexed corpora available via the `gbrain` CLI:
- This worktree's code (auto-pinned via `.gbrain-source` → `orama-src`).
- `~/.gstack/` curated memory (registered as `gstack-brain-lawrencecyremelgarejo` source).

Prefer gbrain when:
- "Where is X handled?" / semantic intent, no exact string yet:
    `gbrain search "<terms>"` or `gbrain query "<question>"`
- "Where is symbol Y defined?" / symbol-based code questions:
    `gbrain code-def <symbol>` or `gbrain code-refs <symbol>`
- "What calls Y?" / "What does Y depend on?":
    `gbrain code-callers <symbol>` / `gbrain code-callees <symbol>`
- "What did we decide last time?" / past plans, retros, learnings:
    `gbrain search "<terms>" --source gstack-brain-lawrencecyremelgarejo`

Grep is still right for known exact strings, regex, multiline patterns, and
file globs. Run `/sync-gbrain` after meaningful code changes.

<!-- gstack-gbrain-search-guidance:end -->
