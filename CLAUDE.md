# orama-system — Claude Code Mandatory Rules

> This file is loaded by Claude Code at the start of every session.
> All rules below are **non-negotiable** for every agent (ECC, AutoResearcher, Claude).
>
> **Repo renamed**: ultrathink-system → orama-system (2026-04-20, ὅραμα = vision/revelation)
> GitHub: <https://github.com/diazMelgarejo/orama-system>

---

## 1. Continuous Learning — Always On

Every session **must** use [continuous-learning-v2](https://github.com/affaan-m/everything-claude-code/tree/main/skills/continuous-learning-v2).

- **Read first**: Load `.claude/lessons/LESSONS.md` at session start — this is the shared knowledge base across all agents and sessions.
- **Write back**: Append meaningful discoveries, patterns, and decisions to `.claude/lessons/LESSONS.md` before ending a session.
- **Instinct path**: Repo instincts live at `.claude/homunculus/instincts/inherited/orama-system-instincts.yaml`.

## 2. ECC Post-Merge Workflow (Mandatory)

After **any** ECC Tools PR is merged into this repo, immediately run:

```bash
# 1. Pull latest
git pull origin main

# 2. Import instincts (run in Claude Code)
/instinct-import .claude/homunculus/instincts/inherited/orama-system-instincts.yaml

# 3. Verify
/instinct-status

# 4. Commit any changes written by the import
git add -A && git commit -m "chore(ecc): post-merge instinct import sync"
git push origin main
```

Or use the `/ecc-sync` command (`.claude/commands/ecc-sync.md`).

## 3. Shared Lessons Path

The canonical lessons file is **`docs/LESSONS.md`** (previously `.claude/lessons/LESSONS.md`, which now redirects here).

- ECC agents: read + write
- AutoResearcher agents: read + write
- Claude sessions: read at start, append before exit
- Auditable on GitHub at all times

| Resource | Purpose |
| --- | --- |
| [`SKILL.md`](SKILL.md) | **Start here.** Agent behavioral rules — every "never" with commands |
| [`docs/LESSONS.md`](docs/LESSONS.md) | Chronological session log — all agents, all dates |
| [`docs/wiki/README.md`](docs/wiki/README.md) | Wiki index — links to all lesson deep-dives |
| [`docs/wiki/06-multi-agent-collab.md`](docs/wiki/06-multi-agent-collab.md) | Version registry, scope claims, orphan branch recovery |

## 4. AutoResearcher Integration

Primary mode: **uditgoenka/autoresearch Claude Code plugin** (runs anywhere).
Secondary mode: GPU runner via SSH for `ml-experiment` task types.

### Plugin install (one-time, idempotent)

```bash
claude plugin marketplace add uditgoenka/autoresearch
claude plugin install autoresearch@autoresearch
```

### Activation (per session)

```claude
/autoresearch          # research loop
/autoresearch:debug    # verbose reasoning trace
```

### Hardware guard — Windows sequential load rule

Never configure the system to load more than one model at a time on the
Windows GPU. Check `swarm_state.md` for `GPU: BUSY` before dispatching any
new experiment. This is enforced in the autoresearcher SOUL.md.

When running AutoResearcher swarms:

- Read `.claude/lessons/LESSONS.md` for prior experiment context
- Record new findings in `.claude/lessons/LESSONS.md` under a dated session entry
- Cross-reference Perpetua-Tools' `.claude/lessons/LESSONS.md` for joint context
- `AUTORESEARCH_REMOTE` env var selects the fork (default: uditgoenka/autoresearch)
- `AUTORESEARCH_BRANCH` env var selects the sync branch (default: main)

## 5. Mother Skill — Always Load

Before any significant change to this repo, load the mother skill:

```claude
/skill bin/orama-system/SKILL.md
```

- Run **AFRP gate** before generating non-trivial output
- Apply **CIDF `decide()`** before any content insertion
- Use **`@field_validator`** (Pydantic V2), never deprecated `@validator`
- Keep orama API **stateless** (no Redis dependency)

## 6. Repository Identity And Git Hygiene

- **Package**: `@diazmelgarejo/orama-system@0.9.9.8`
- **Role**: Application / Orchestration / Meta-Intelligence (Layer 3 of the three-repo architecture)
- **Previous identity**: orama-system (ultrathink POST /ultrathink on port 8001)
- **Companion repos**:
  - [AlphaClaw](https://github.com/diazMelgarejo/AlphaClaw) (Layer 1 — infrastructure)
  - [Perpetua-Tools](https://github.com/diazMelgarejo/Perpetua-Tools) (Layer 2 — adapters/middleware)
- **Skill**: `.claude/skills/orama-system/SKILL.md` (renamed from: `ultrathink-system/SKILL.md`)
- **Mother skill**: `bin/orama-system/SKILL.md` (v0.9.9.7 → 0.9.9.8 after migration)

Git hygiene rules for clean-lineage work:

- Commit identity must be `cyre <Lawrence@cyre.me>`; verify with `bash scripts/git/check_identity.sh`.
- Use dated branches: `yyyy-mm-dd-001-brief-summary`.
- Before risky Git work, snapshot status and stash with untracked files.
- Do not commit `.env`, `.env.local`, or generated `.paths`; update `.env.example` and `.paths.example` instead.
- Do not replay polluted commits directly; manual-port reviewed intent into new commits with detailed conventional bodies.

## 7. Three-Repo Architecture (read before any significant work)

```ascii
AlphaClaw (Layer 1 — infrastructure)
    │  CLI + HTTP only
    ▼
Perpetua-Tools (Layer 2 — middleware/adapters)
    │  typed adapter contracts → PT drives AlphaClaw
    ▼
orama-system (Layer 3 — THIS REPO — orchestration/meta-intelligence)
```

### What lives in orama (existing + new)

| Path | Purpose |
|------|---------|
| `bin/mcp_servers/openclaw_bridge.py` | AlphaClaw bridge (foundation — extends to use PT adapter) |
| `bin/mcp_servers/openclaw_mcp_server.py` | MCP server wrapping AlphaClaw operations |
| `bin/mcp_servers/ultrathink_orchestration_server.py` | orama orchestration MCP server |
| `bin/agents/orchestrator/` | Multi-agent orchestrator with SOUL.md |
| `bin/agents/{architect,coder,crystallizer,executor,...}/` | Specialized agent definitions |
| `bin/shared/bridge_contract.py` | Inter-agent messaging contract |
| `bin/shared/message_bus.py` | Agent message bus |
| `bin/orama-system/` | AFRP, CIDF, and other skill frameworks |
| `observability/` | Gate 3: OTel emitter, Tempo, Grafana (see system-design §6) |

### AlphaClaw integration (via Perpetua-Tools adapter)

orama talks to AlphaClaw through PT's adapter, not directly:

```
orama orchestrator → PT adapter APIs → AlphaClaw HTTP/CLI
```

`bin/mcp_servers/openclaw_bridge.py` currently calls AlphaClaw directly. Gate 3 work: route through PT's typed adapter contract instead.

### Lifecycle delegation — Gate 1+ (CRITICAL)

`start.sh` now delegates ALL gateway/backend decisions to PT:

```bash
eval "$(python -m orchestrator.alphaclaw_manager --resolve --env-only)"
```

- `orchestrator/alphaclaw_manager.py` in PT owns: backend probe, mode determination, AlphaClaw bootstrap
- orama's `start.sh` is a **pure process manager** — it reads PT's resolved payload and starts services
- Never add gateway routing logic back to `start.sh` — that violates the PT-is-authoritative invariant

**Files NOT to modify without understanding the invariant:**

- `start.sh` — thin delegator; any new gateway logic must go to PT's `alphaclaw_manager.py`
- `openclaw_bootstrap.py` — scope-down to apply-config only is Gate 2; do not add probe logic here

### Key invariants (carried over from orama-system)

- orama API stays **stateless** — no Redis dependency
- Windows GPU: load ONE model at a time (check `GPU: BUSY` in swarm_state.md)
- AFRP gate before any non-trivial output generation
- CIDF `decide()` before any content insertion
- `@field_validator` (Pydantic V2), never deprecated `@validator`

## 8. Harness Path Map

| Source | Runtime | Harness |
|--------|---------|---------|
| `bin/orama-system/SKILL.md` | `.claude/skills/orama-system/SKILL.md` | Claude Code (project) |
| `bin/orama-system/SKILL.md` | `~/.claude/skills/orama-system/` | Claude Code (global) |
| `bin/orama-system/SKILL.md` | `.agents/skills/orama-system/SKILL.md` | Codex/OpenCode |
| `bin/agents/*/` | `.claude/agents/ultrathink-*.md` | Claude Code subagents |

> CIDF content (`bin/orama-system/cidf/`) is the canonical source. Install scripts copy it to
> `.claude/skills/orama-system/cidf/` and `.agents/skills/orama-system/cidf/`
> at runtime; checked idempotently on each run.

## 9. gstack

gstack v1.12.2.0 is installed at `~/.claude/skills/gstack` (global-git) as the agent skill framework for web browsing, planning, and review.

**Rules:**

- ALWAYS use `/browse` for all web browsing — NEVER use `mcp__claude-in-chrome__*` tools directly
- Use `/investigate` for root-cause analysis of adapter or orchestration failures
- Use `/ship` before any `npm publish`

**Available skills:**

| Skill | Purpose |
|-------|---------|
| `/browse` | Headless browser for web browsing and site docs |
| `/qa` | Systematically QA test a web application and fix issues |
| `/qa-only` | Report-only QA testing |
| `/design-review` | Designer's eye QA: visual inconsistency, spacing, contrast |
| `/design-html` | Generate production-quality HTML designs |
| `/design-shotgun` | Generate multiple AI design variants |
| `/design-consultation` | Understand your product and provide design guidance |
| `/review` | Pre-landing PR review |
| `/ship` | Ship workflow: detect + merge base branch, run tests, deploy |
| `/land-and-deploy` | Land and deploy workflow |
| `/canary` | Post-deploy canary monitoring |
| `/benchmark` | Performance regression detection |
| `/office-hours` | YC Office Hours — startup or project mode |
| `/plan-ceo-review` | CEO/founder-mode plan review |
| `/plan-eng-review` | Eng manager-mode plan review |
| `/plan-design-review` | Designer's eye plan review |
| `/plan-devex-review` | Interactive developer experience plan review |
| `/autoplan` | Auto-review pipeline |
| `/devex-review` | Live developer experience audit |
| `/retro` | Weekly engineering retrospective |
| `/investigate` | Systematic debugging with root cause investigation |
| `/document-release` | Post-ship documentation update |
| `/codex` | OpenAI Codex CLI wrapper |
| `/cso` | Chief Security Officer mode |
| `/learn` | Manage project learnings |
| `/careful` | Safety guardrails for destructive commands |
| `/freeze` | Restrict file edits to a specific directory |
| `/unfreeze` | Clear the freeze boundary set by /freeze |
| `/guard` | Full safety mode: destructive command warnings |
| `/setup-browser-cookies` | Import cookies from real Chromium browser |
| `/setup-deploy` | Configure deployment settings |
| `/setup-gbrain` | Set up gbrain for this coding agent |
| `/connect-chrome` | Pair a remote AI agent with your browser |
| `/gstack-upgrade` | Upgrade gstack to the latest version |

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. The
skill has multi-step workflows, checklists, and quality gates that produce better
results than an ad-hoc answer. When in doubt, invoke the skill. A false positive is
cheaper than a false negative.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke /office-hours
- Strategy, scope, "think bigger", "what should we build" → invoke /plan-ceo-review
- Architecture, "does this design make sense" → invoke /plan-eng-review
- Design system, brand, "how should this look" → invoke /design-consultation
- Design review of a plan → invoke /plan-design-review
- Developer experience of a plan → invoke /plan-devex-review
- "Review everything", full review pipeline → invoke /autoplan
- Bugs, errors, "why is this broken", "wtf", "this doesn't work" → invoke /investigate
- Test the site, find bugs, "does this work" → invoke /qa (or /qa-only for report only)
- Code review, check the diff, "look at my changes" → invoke /review
- Visual polish, design audit, "this looks off" → invoke /design-review
- Developer experience audit, try onboarding → invoke /devex-review
- Ship, deploy, create a PR, "send it" → invoke /ship
- Merge + deploy + verify → invoke /land-and-deploy
- Configure deployment → invoke /setup-deploy
- Post-deploy monitoring → invoke /canary
- Update docs after shipping → invoke /document-release
- Weekly retro, "how'd we do" → invoke /retro
- Second opinion, codex review → invoke /codex
- Safety mode, careful mode, lock it down → invoke /careful or /guard
- Restrict edits to a directory → invoke /freeze or /unfreeze
- Upgrade gstack → invoke /gstack-upgrade
- Save progress, "save my work" → invoke /context-save
- Resume, restore, "where was I" → invoke /context-restore
- Security audit, OWASP, "is this secure" → invoke /cso
- Make a PDF, document, publication → invoke /make-pdf
- Launch real browser for QA → invoke /open-gstack-browser
- Import cookies for authenticated testing → invoke /setup-browser-cookies
- Performance regression, page speed, benchmarks → invoke /benchmark
- Review what gstack has learned → invoke /learn
- Tune question sensitivity → invoke /plan-tune
- Code quality dashboard → invoke /health
