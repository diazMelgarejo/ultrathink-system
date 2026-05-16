# Salvage Code Translation — Design Spec

**Date:** 2026-05-17
**Status:** Approved (brainstorm), pending implementation plan
**Author:** Opus 4.7 (controller) + user (decision-maker)
**Companion to:** `2026-05-14-salvage-plugins-design.md` (selection spec) — this file covers **port mechanics**

> **For agentic workers:** This is a design doc, NOT an implementation plan. Read fully before any port work begins. Implementation plan will be generated separately via `superpowers:writing-plans` skill.

---

## §1 — Scope

Port valuable assets from wrong-repo `diazMelgarejo/perpetua-core@9cb153a` into canonical `oramasys/perpetua-core@2f717f5` plugin structure.

### Working salvage list (revisitable per-plugin during port)

| Asset | Origin (wrong-repo) | Destination (canonical) |
|---|---|---|
| `tool_node` plugin | `perpetua_core/graph/nodes.py` `ToolNode` class (87 lines) | `perpetua_core/graph/plugins/tool_node.py` |
| `routing` plugin | `perpetua_core/graph/edges.py` `ConditionalEdge` (67 lines) | `perpetua_core/graph/plugins/routing.py` |
| `validator` plugin | (synthesized from spec — wrong-repo had no validator) | `perpetua_core/graph/plugins/validator.py` |
| `interrupt_guard` plugin | (synthesized — see open question) | `perpetua_core/graph/plugins/interrupt_guard.py` OR merged into canonical `interrupts.py` |
| `set_entry()` engine method | `perpetua_core/graph/engine.py:set_entry()` (~5 lines) | `perpetua_core/graph/engine.py` (engine addition) |
| `compile()` engine method | `perpetua_core/graph/engine.py:compile()` + lazy-compile guard (~10 lines) | `perpetua_core/graph/engine.py` (engine addition) |

### Open considerations (decide per-plugin at port time)

- **`ConditionalEdge.mapping`** (label→node resolution) — port into `routing` plugin?
- **`interrupt_guard`** — merge with canonical `graph/plugins/interrupts.py`, or ship separately?
- **State fields** `nodes_visited: list[str]` and `retry_count: int` (per Grok synthesis) — add to canonical `state.py`?

---

## §2 — Architecture constraints

Canonical structure already correct: **65-line pure engine** + `graph/plugins/*.py` directory. Ports MUST conform.

### Non-negotiable invariants

| Invariant | Source | Status |
|---|---|---|
| Engine ≤ 80 lines after port | D8 revision | hard |
| Each plugin file ≤ 80 lines | matches existing canonical plugin shape | soft (sane default) |
| `PerpetuaState` is `BaseModel` (not dataclass) | D7 | hard |
| `scratchpad: dict[str, Any]` (not `str`) | D8 | hard |
| Async `aiosqlite` (not sync `sqlite3`) | OQ11 resolution | hard |
| Python 3.11+ (`requires-python = ">=3.11"`) | OQ7 resolution | hard |
| Plugin protocol matches existing shape | `tool.py`, `streaming.py`, `checkpointer.py` | hard |

### Idiom translation rules (apply mechanically during port)

| Wrong-repo idiom | Canonical idiom |
|---|---|
| `from pydantic.dataclasses import dataclass; @dataclass class X` | `from pydantic import BaseModel, ConfigDict; class X(BaseModel)` |
| `scratchpad: str = ""` | `scratchpad: dict[str, Any] = Field(default_factory=dict)` |
| `import sqlite3; conn = sqlite3.connect(...)` | `import aiosqlite; async with aiosqlite.connect(...) as conn` |
| `class Edge: ...` / `class ConditionalEdge: ...` | callable in `add_edge(source, callable_or_target)` |
| `END = "__end__"` only | both `START` and `END` sentinels from canonical |
| Subprocess via `subprocess.run()` | `asyncio.create_subprocess_exec()` (async) |
| Integrated streaming in engine | extend canonical `graph/plugins/streaming.py` |

---

## §3 — Labor split (multi-agent)

Per plugin, four roles work in sequence (with parallelization across plugins):

| Stage | Tool | MCP entry point | Output |
|---|---|---|---|
| **Read + translate-table** | Gemini Pro | `mcp__gemini-cli__ask-gemini` (model=pro) | `salvage/<plugin>/translation-table.md` — three columns: wrong-repo line/concept, canonical idiom translation, target plugin shape |
| **Write plugin + tests** | Codex | `mcp__ai-cli__run` (model=`gpt-5.2-codex`) | `perpetua_core/graph/plugins/<plugin>.py` + `tests/test_<plugin>.py` |
| **Review against canonical** | Claude Sonnet 4.6 | `mcp__ai-cli__run` (model=`sonnet`) | Pass/fail verdict + diff comments referencing canonical's 32 tests |
| **Orchestrate + decide** | Claude Opus 4.7 (this session) | — | C-feature decisions (mapping/merge/state fields); integration; commit |

### Merge-where-possible discipline

When two plugins share translation idioms (e.g., both use `state.scratchpad` dict access pattern), Gemini's tables are **unified** across them; Codex receives the unified table to avoid duplicate work. Examples of unifiable concerns:

- Async subprocess pattern (used by `tool_node` and possibly `validator`)
- Plugin protocol boilerplate (used by all 4 plugins)
- Test fixtures for synthetic `PerpetuaState` (used by all plugin tests)

---

## §4 — Branch + resumability discipline

### Branch model

- **Working branch:** `feat/salvage-plugins-rc1` in `/Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core` (local only — **no push to `oramasys/*` without AFRP gate**)
- **Branch source of truth:** this spec; branch name is **pinned** so any agent that picks up work pushes to the same branch
- **Atomic commits:** one logical port per commit. Conventional Commits format: `feat(plugin): port tool_node from wrong-repo` / `feat(engine): add set_entry + compile methods`
- **Revert-clean:** any single commit can be `git revert <sha>`-ed without affecting other ports

### Living tasklist — `PROGRESS.md` at branch root

Required structure:

```markdown
# Salvage Port Progress

Branch: feat/salvage-plugins-rc1
Spec: docs/superpowers/specs/2026-05-17-salvage-translation-design.md (in orama-system repo)
Last updated: <ISO date> by <agent-id>

## Wave 0 — Translation tables (parallel)
| Item | State | Owner | Commit |
|---|---|---|---|
| engine-methods translation table | queued | — | — |
| tool_node translation table | queued | — | — |
| routing translation table | queued | — | — |
| validator translation table | queued | — | — |
| interrupt_guard triage table | queued | — | — |
| state-fields translation table | queued | — | — |

## Wave 1 — Engine foundation
| Item | State | Owner | Commit |
|---|---|---|---|
| set_entry + compile + lazy guard | queued | — | — |

## Wave 2 — Independent ports (parallel)
| Item | State | Owner | Commit |
|---|---|---|---|
| tool_node plugin | queued | — | — |
| state fields (if approved) | queued | — | — |
| interrupt_guard merge/drop decision | queued | — | — |

## Wave 3 — Engine-dependent ports (parallel)
| Item | State | Owner | Commit |
|---|---|---|---|
| routing plugin | queued | — | — |
| validator plugin | queued | — | — |

## Wave 4 — Integrative decisions
| Item | State | Owner | Commit |
|---|---|---|---|
| Finalize C-features | queued | — | — |
| Final AFRP review | queued | — | — |

## Architecture revisions proposed
(empty — populated as discoveries happen; see §9)
```

### State machine per row

`queued` → `gemini-read` → `codex-write` → `sonnet-review` → `integrated` → `committed`

Every state transition is one Markdown line edit committed in the same commit as the work. Use git as the audit trail.

### Claim mechanism (multi-agent coordination)

Before any agent starts work on a row:

1. Edit `PROGRESS.md` row to set `Owner: <agent-id>` (e.g., `Owner: opus-4.7-session-abc123`)
2. `git commit -m "chore: claim <item>"` and push immediately
3. If push fails (another agent claimed it first), `git pull --rebase`, see new owner, pick a different row

This is git-native distributed locking — atomic at the commit level, no separate lock service needed.

---

## §5 — TDD discipline (full)

Per plugin, **in this order**:

1. **Red:** write failing unit tests in `tests/test_<plugin>.py` against wished-for API. Confirm RED.
2. **Green:** Codex ports code from wrong-repo using Gemini's translation table. Run tests. Confirm GREEN.
3. **Integration:** add `tests/test_integration_wave<N>.py` wiring this plugin into a multi-plugin MiniGraph with at least one other plugin (e.g., `tool_node` + `routing` in one graph). Run, confirm pass.
4. **Property-based** (engine methods only): `tests/test_engine_properties.py` using Hypothesis. Required properties:
   - `compile()` is idempotent: `g.compile(); g.compile()` ≡ `g.compile()`
   - `set_entry(X)` then `ainvoke()` always starts execution at node X
   - `compile()` failures do not mutate the graph
   - `add_node()` / `add_edge()` after `compile()` raise `RuntimeError` (graph is frozen)
5. **Regression gate:** all 32 canonical tests still pass. Run: `pytest tests/ -v`.
6. **Commit only if all of 1–5 pass.**

### Test dependencies

- Add `hypothesis` to `[tool.poetry.group.dev.dependencies]` in canonical `pyproject.toml` (Wave 1, one-time).
- Reuse canonical's existing `pytest` + `pytest-asyncio` setup (no new test runners).

### Test naming conventions (match canonical)

- `tests/test_<plugin>.py` — unit tests
- `tests/test_integration_wave<N>.py` — wave-scoped integration tests
- `tests/test_engine_properties.py` — property-based (engine only)

---

## §6 — Ordering (waved hybrid)

| Wave | Items | Mode | Gate to next wave |
|---|---|---|---|
| **0** | All translation tables (engine + 4 plugins + state fields + interrupt_guard triage) | 6 parallel `mcp__gemini-cli__ask-gemini` calls | All 6 tables landed in `salvage/<plugin>/translation-table.md` and committed |
| **1** | Engine methods (`set_entry` + `compile` + lazy-compile guard) | Sequential: 1 Codex write + 1 Sonnet review + Opus integrate | **AFRP gate** (Opus + user). 32 canonical tests green + new property-based tests green. Engine still ≤ 80 lines. |
| **2** | `tool_node` plugin · state fields (if approved) · `interrupt_guard` merge/drop decision | 3 concurrent Codex workers; 3 concurrent Sonnet reviewers; Opus integrates | All 3 green: unit + integration + regression |
| **3** | `routing` plugin (with mapping decision) · `validator` plugin | 2 concurrent Codex workers; 2 concurrent Sonnet reviewers; Opus integrates | Integration tests for combined plugin graphs pass |
| **4** | Finalize C-features (mapping/merge/state fields) based on discoveries from Waves 2–3 | Opus + user | **Final AFRP gate** + decision to push branch to `oramasys/perpetua-core` |

### Critical path

Wave 0 is read-only — cheap. Wave 1 must be sequential (foundation). Waves 2 + 3 maximize parallelism. Wave 4 is the only place "what we learned" becomes "what we change."

### Dependency invariants

- Nothing in Wave 2 depends on Wave 2 (truly parallel)
- Wave 3 depends only on Wave 1 (engine methods landed)
- Wave 4 depends on Waves 2 + 3 having surfaced discoveries

---

## §7 — Out of scope / decided "never port"

| Wrong-repo asset | Why never port |
|---|---|
| `state.py` `pydantic.dataclasses.dataclass` form | Canonical `BaseModel` wins per D7 |
| `scratchpad: str` | Canonical `dict[str, Any]` wins per D8 |
| Sync `gossip.py` `sqlite3` | Canonical `aiosqlite` wins per OQ11 |
| Generic `Edge` class | Canonical callable-in-`add_edge` is simpler |
| Integrated streaming in engine | Canonical `graph/plugins/streaming.py` already correct |
| Integrated HITL `Interrupt` in engine | Canonical `graph/plugins/interrupts.py` already correct (modulo `interrupt_guard` open question) |
| Integrated subgraph support in engine | Canonical `graph/plugins/subgraphs.py` already correct |
| Wrong-repo's smoke `tests/test_smoke.py` | Canonical's 32 tests already cover smoke + more |

---

## §8 — Companion deliverables (ride-along, NOT in this spec's scope)

These ship in the same commit/push as this spec for "harmonize all before commit":

### 8.1 — `--mirror-skills` flag (direct implementation, no sub-spec)

Add `--mirror-skills` to `bin/orama-system/scripts/install-mcp-stack.sh` (~30 lines bash). Behavior:

- Copies SKILL.md files from `bin/orama-system/*/SKILL.md` to platform skill directories:
  - `~/.claude/skills/<name>/SKILL.md` (Claude Code)
  - `~/.codex/skills/<name>/SKILL.md` (Codex CLI)
  - `~/.gemini/skills/<name>/SKILL.md` (Gemini CLI, if directory exists)
  - OpenClaw skill registry path (via `openclaw skill set <name> <path>` if `openclaw` CLI present)
- Idempotent: skip targets that already match (sha256 compare)
- Dry-run safe: respects existing `--dry-run` flag
- Verbose: prints `[mirror] <src> → <dst>` for each operation
- Fails closed: if a target dir doesn't exist AND its tool is detected as installed, fail; if tool is absent, skip silently

7 skills to mirror: `mother SKILL.md`, `mcp-install`, `mcp-orchestration`, `gstack`, `cidf`, `skillify`, `afrp`.

### 8.2 — LESSONS.md note about portal visual fluidity

Append a single-paragraph note to `docs/LESSONS.md`:

> **2026-05-17 — Operator console mockup is inspirational, not binding.** The generated 1440×1000 mockup of the orama Command Center captures the *aesthetic direction* (dark charcoal/slate panels, accent cyan, dense typography, segmented controls, table-heavy layouts) — it is NOT a pixel-binding contract. Implementation may diverge from layout, copy, and icon details as long as the aesthetic direction holds. Future visual upgrades should reference the mockup as a tone-setting reference, not a spec.

---

## §9 — Architectural revision protocol (microkernel reshape permission)

The port itself is a **stress-test** of the canonical microkernel + plugin architecture. If porting reveals the kernel/plugin protocol could be sharper, early-days reshaping is allowed and welcome — bounded by this protocol.

### In-scope revisions (can be proposed during port)

- Tightening the `GraphPlugin` protocol if porting shows current shape is over/under-specified
- Adding plugin lifecycle hooks (`init` / `teardown` / `on_compile`) if multiple ports need them
- Renaming engine internals (variables, helpers) if porting exposes naming friction
- Introducing explicit plugin registration discipline vs duck-typing
- Adjusting `state.merge()` semantics if port reveals merge edge cases
- Refining the START/END sentinel surface or `ainvoke` signature

### Revision proposal flow

1. **Surface** in `PROGRESS.md` under `## Architecture revisions proposed`:
   - Discoverer (agent-id), plugin/wave context, proposed change, blast radius (which files/tests affected), recommended decision
2. **AFRP gate**: Opus + user evaluate scope/cost/value
3. **Decide**: accept · defer (note rationale) · reject (note rationale)
4. **If accepted**: revision lands as a **separate atomic commit BEFORE** any port commits that depend on it. Add commit to PROGRESS.md.
5. **Document** in `docs/architectural-decisions.md` in the canonical repo (create if missing). Format: ADR-NNN per Michael Nygard's pattern.

### Out-of-scope revisions

- Rewriting the 65-line engine wholesale
- Changing `BaseModel` / `aiosqlite` / Python 3.11+ decisions
- Removing existing plugins (`interrupts.py`, `streaming.py`, `tool.py`, etc.)
- Changing the `oramasys/perpetua-core` repo home

### Spirit

The canonical kernel shipped 16 days ago. This spec was written before any port stress-test. **Surface friction is expected and welcome** — but bounded, not a blank check.

---

## §10 — Definition of Done

The salvage port is **DONE** when:

1. All Wave 0 translation tables committed to canonical branch.
2. Wave 1 engine methods (`set_entry`, `compile`) landed, all canonical tests green + property-based tests green.
3. Wave 2 ports landed (`tool_node` + state-fields decision + `interrupt_guard` decision).
4. Wave 3 ports landed (`routing` + `validator`).
5. Wave 4 integrative decisions finalized.
6. All canonical 32 tests + new unit tests + new integration tests + new property-based tests green.
7. `PROGRESS.md` shows every row `committed`.
8. `docs/architectural-decisions.md` records any accepted revisions.
9. User approves push of `feat/salvage-plugins-rc1` → `oramasys/perpetua-core` main (AFRP gate cleared).
10. After push: tag canonical `v0.2.0-alpha` (or per user's versioning preference).

---

## References

- Selection spec: [`2026-05-14-salvage-plugins-design.md`](2026-05-14-salvage-plugins-design.md) — *what* to port, this spec covers *how*.
- Wrong-repo post-mortem: [`docs/wiki/10-wrong-repo-build-what-not-to-do.md`](../../wiki/10-wrong-repo-build-what-not-to-do.md)
- Canonical repo: `/Users/lawrencecyremelgarejo/Documents/oramasys/perpetua-core` (commit `2f717f5`)
- Wrong-repo: `/Users/lawrencecyremelgarejo/Documents/Terminal xCode/claude/OpenClaw/perpetua-core` (commit `9cb153a`, remote `diazMelgarejo/perpetua-core`)
- TDD discipline: `docs/TDD.md` + `superpowers:test-driven-development` skill
- AFRP gate: `bin/orama-system/afrp/SKILL.md`
- MCP orchestration: `bin/orama-system/mcp-orchestration/SKILL.md`
